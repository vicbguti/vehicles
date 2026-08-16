from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

from fleet_loading.pipelines.training.pairwise import (
    build_tensors,
    derive_classes,
    evaluate_split,
    measure_latency,
    select_policy,
    stack_episode_logits,
)
from src.modeling.capacity_decoder import DEFERRED, decode_episode

DEFER_LABEL = 0  # canonical index of SIN_CAMION (index 0, trucks 1..T)

# Versioned model artifacts. Same root ``nodes.py`` uses for the GBTs; it lived
# inline inside ``_save_attention_artifact`` as a second copy of the same
# ``parents[5]`` path arithmetic.
ARTIFACT_ROOT = Path(__file__).resolve().parents[5] / "artifacts" / "fleet_loading"


class EpisodeDataset(Dataset):
    """One item per episode: canonical pairwise tensors from src/modeling.

    The truck axis is dynamic: ``truck`` is ``(T, Dt)`` with T the episode's real
    truck count (no MAX_TRUCKS padding), so the model accepts any number of
    trucks at inference with the same weights.
    """

    def __init__(self, df: pd.DataFrame, classes: list[str], scaler=None):
        self.episodes, self.arrays, self.scaler = build_tensors(df, classes, scaler)
        self.classes = classes

    def __len__(self):
        return len(self.episodes)

    def __getitem__(self, idx):
        ep = self.episodes[idx]
        vehicle = self.scaler.transform("vehicle", ep.vehicle)
        truck = self.scaler.transform("truck", ep.truck)
        context = self.scaler.transform("context", ep.context[None, :])[0]
        return {
            "vehicle": torch.from_numpy(vehicle.astype(np.float32)),
            "truck": torch.from_numpy(truck.astype(np.float32)),
            "context": torch.from_numpy(context.astype(np.float32)),
            "labels": torch.from_numpy(ep.target.astype(np.int64)),
            "cu": torch.from_numpy(ep.cu.astype(np.float32)),
            "capacities": torch.from_numpy(ep.capacities.astype(np.float32)),
            "episode_id": ep.episode_id,
            "n_trucks": ep.n_trucks,
            "teacher_n_loaded": ep.teacher_n_loaded,
            "teacher_cu_utilized": ep.teacher_cu_utilized,
        }


def collate_episodes(batch):
    max_n = max(item["labels"].shape[0] for item in batch)
    max_t = max(item["n_trucks"] for item in batch)
    vehicle_dim = batch[0]["vehicle"].shape[1]
    truck_dim = batch[0]["truck"].shape[1]
    context_dim = batch[0]["context"].shape[0]
    n_eps = len(batch)

    vehicle = torch.zeros(n_eps, max_n, vehicle_dim)
    truck = torch.zeros(n_eps, max_t, truck_dim)
    context = torch.zeros(n_eps, context_dim)
    labels = torch.full((n_eps, max_n), -100, dtype=torch.long)
    cu = torch.zeros(n_eps, max_n)
    capacities = torch.zeros(n_eps, max_t)
    pad_mask = torch.ones(n_eps, max_n, dtype=torch.bool)
    truck_mask = torch.ones(n_eps, max_t, dtype=torch.bool)

    for i, item in enumerate(batch):
        n, t = item["labels"].shape[0], item["n_trucks"]
        vehicle[i, :n] = item["vehicle"]
        truck[i, :t] = item["truck"]
        context[i] = item["context"]
        labels[i, :n] = item["labels"]
        cu[i, :n] = item["cu"]
        capacities[i, :t] = item["capacities"]
        pad_mask[i, :n] = False
        truck_mask[i, :t] = False

    return {
        "vehicle": vehicle,
        "truck": truck,
        "context": context,
        "labels": labels,
        "cu": cu,
        "capacities": capacities,
        "pad_mask": pad_mask,
        "truck_mask": truck_mask,
        "episode_ids": [item["episode_id"] for item in batch],
        "n_trucks": torch.tensor([item["n_trucks"] for item in batch]),
    }


class PairwiseAttentionModel(nn.Module):
    """Transformer over the vehicle set with a pairwise (vehicle, truck) head.

    Same canonical feature blocks as the MLP/GBTs (src/modeling): vehicle
    block (V, Dv), truck block (T, Dt), context (Dg). The transformer mixes
    vehicle context; a shared pairwise head scores each (vehicle, truck) and a
    separate defer head scores SIN_CAMION, concatenated into (V, 1 + T) logits
    with SIN_CAMION at index 0. T is fully dynamic.
    """

    def __init__(
        self,
        vehicle_dim: int,
        truck_dim: int,
        context_dim: int,
        d_model: int = 64,
        nhead: int = 4,
        num_layers: int = 3,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.d_model = d_model
        self.vehicle_proj = nn.Linear(vehicle_dim, d_model)
        self.context_proj = nn.Linear(context_dim, d_model)
        self.truck_proj = nn.Linear(truck_dim, d_model)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        self.pair_head = nn.Sequential(
            nn.Linear(d_model * 2, d_model),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, 1),
        )
        self.defer_head = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, 1),
        )

    def forward(self, batch):
        vehicle = batch["vehicle"]
        truck = batch["truck"]
        context = batch["context"]
        pad_mask = batch["pad_mask"]
        truck_mask = batch["truck_mask"]  # True on padding trucks

        v = self.vehicle_proj(vehicle)  # (B, V, d)
        g = self.context_proj(context).unsqueeze(1)  # (B, 1, d)
        v = v + g
        h = self.transformer(v, src_key_padding_mask=pad_mask)  # (B, V, d)

        t = self.truck_proj(truck)  # (B, T, d)
        B, V, T = h.shape[0], h.shape[1], t.shape[1]
        hv = h[:, :, None, :].expand(B, V, T, self.d_model)
        tv = t[:, None, :, :].expand(B, V, T, self.d_model)
        pair = self.pair_head(torch.cat([hv, tv], dim=-1)).squeeze(-1)  # (B, V, T)
        pair = pair.masked_fill(truck_mask[:, None, :], -1e9)

        defer = self.defer_head(h).squeeze(-1)  # (B, V)
        logits = torch.cat([defer.unsqueeze(-1), pair], dim=-1)  # (B, V, 1+T)
        return logits


@torch.no_grad()
def predict_with_capacity(
    logits: torch.Tensor,
    cu: torch.Tensor,
    capacities: torch.Tensor,
    n_trucks_arr: torch.Tensor,
    pad_mask: torch.Tensor,
    policy: str,
) -> torch.Tensor:
    """Capacity-aware per-episode assignment via ``capacity_decoder.decode_episode``.

    ``policy`` used to be hardcoded to ``"model"`` here while
    ``attention_operational_report`` used the policy chosen on validation. Both
    paths fed published numbers, so the transformer shipped **three** different
    val figures -- raw argmax, this decoder, and the operational one -- and the
    two decoded ones never reconciled. There is one decoder and one policy per
    run; it comes in as an argument so it cannot drift again.
    """
    batch_size, max_n, _ = logits.shape
    preds = torch.full((batch_size, max_n), -100, dtype=torch.long, device=logits.device)

    for b in range(batch_size):
        n = max_n - pad_mask[b].sum().item()
        n_trucks = int(n_trucks_arr[b].item())
        ep_logits = logits[b, :n, : n_trucks + 1].cpu().numpy()
        decoded = decode_episode(
            ep_logits,
            cu=cu[b, :n].cpu().numpy(),
            capacities=capacities[b, :n_trucks].cpu().numpy(),
            policy=policy,
        )
        assignment = np.where(decoded.assignment == DEFERRED, 0, decoded.assignment + 1)
        preds[b, :n] = torch.from_numpy(assignment.astype(np.int64))

    return preds


@torch.no_grad()
def _episode_logits_batched(model: nn.Module, loader: DataLoader, device) -> dict[str, np.ndarray]:
    """One batched pass over the loader -> per-episode (V, 1+T) logits, keyed by episode_id."""
    model.eval()
    out = {}
    for batch in loader:
        batch = {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}
        logits = model(batch)
        n_real = batch["labels"].shape[1] - batch["pad_mask"].sum(dim=1)
        n_trucks = batch["n_trucks"]
        for i, ep_id in enumerate(batch["episode_ids"]):
            out[ep_id] = logits[i, : n_real[i], : n_trucks[i] + 1].cpu().numpy()
    return out


def _logits_by_index(episodes, by_id: dict[str, np.ndarray]) -> dict[int, np.ndarray]:
    """Remap per-episode logits keyed by episode_id onto the episode-list order."""
    return {i: by_id[ep.episode_id] for i, ep in enumerate(episodes)}


def attention_operational_report(
    model: nn.Module,
    val_loader: DataLoader,
    val_ds: EpisodeDataset,
    device,
    policy: str,
    val_logits: np.ndarray,
) -> dict:
    """Episode-level report vs teacher using the shared src/modeling metrics."""
    model_metrics, greedy_metrics = evaluate_split(
        val_ds.episodes, val_ds.arrays, val_logits, val_ds.classes, policy
    )
    latency = measure_latency(val_ds.episodes, val_ds.arrays, val_logits, policy)
    return {
        "model": {**model_metrics, "latency": latency},
        "greedy": {**greedy_metrics, "latency": latency},
    }


def _attention_predictions_df(cap_labels_all, cap_preds_all) -> pd.DataFrame:
    """Combine capacity-aware val predictions into a DataFrame for the report node."""
    return pd.DataFrame(
        {
            "y_true": np.concatenate(cap_labels_all),
            "y_pred": np.concatenate(cap_preds_all),
        }
    )


def train_attention(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    episodes: pd.DataFrame,
    d_model: int,
    nhead: int,
    num_layers: int,
    dropout: float,
    batch_size: int,
    learning_rate: float,
    n_epochs: int,
    seed: int,
    run_name: str,
) -> dict:
    import os
    import tempfile
    import warnings

    import mlflow

    warnings.filterwarnings("ignore")

    # Sin esto el entrenamiento no era reproducible por tres vías a la vez:
    # inicialización de pesos, dropout y el orden que `shuffle=True` da a los
    # episodios. Las cifras publicadas no se podían volver a obtener, y en una
    # tabla que compara seis modelos eso hace indistinguible una mejora real de
    # la varianza entre corridas.
    torch.manual_seed(seed)
    np.random.seed(seed)
    generator = torch.Generator().manual_seed(seed)

    classes = derive_classes(train_df)
    train_ds = EpisodeDataset(train_df, classes)
    val_ds = EpisodeDataset(val_df, classes, train_ds.scaler)

    train_loader = DataLoader(
        train_ds,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collate_episodes,
        generator=generator,
    )
    val_loader = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False, collate_fn=collate_episodes
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ep0 = train_ds.episodes[0]
    model = PairwiseAttentionModel(
        vehicle_dim=ep0.vehicle.shape[1],
        truck_dim=ep0.truck.shape[1],
        context_dim=len(ep0.context),
        d_model=d_model,
        nhead=nhead,
        num_layers=num_layers,
        dropout=dropout,
    ).to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=n_epochs)

    train_epochs = []
    val_metrics = []

    for epoch in range(n_epochs):
        model.train()
        total_loss = 0.0
        n_batches = 0
        train_correct = 0
        train_total = 0

        for batch in train_loader:
            batch = {
                k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()
            }
            logits = model(batch)
            labels = batch["labels"]
            n_classes = logits.shape[-1]
            loss = F.cross_entropy(
                logits.reshape(-1, n_classes),
                labels.reshape(-1),
                ignore_index=-100,
            )

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            mask = labels != -100
            preds = logits.argmax(dim=-1)
            train_correct += ((preds == labels) & mask).sum().item()
            train_total += mask.sum().item()

            total_loss += loss.item()
            n_batches += 1

        scheduler.step()
        train_loss = total_loss / n_batches
        train_acc = train_correct / train_total if train_total > 0 else 0.0

        model.eval()
        n_correct = 0
        n_total = 0
        n_def_correct = 0
        n_def_pred = 0
        n_def_actual = 0
        val_loss_total = 0.0
        val_batches = 0

        with torch.no_grad():
            for batch in val_loader:
                batch = {
                    k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()
                }
                logits = model(batch)
                labels = batch["labels"]
                mask = labels != -100

                # La pérdida de validación faltaba: el bucle sacaba exactitud y
                # F1 pero no la pérdida, así que la curva del transformer era la
                # única de los seis modelos sin las dos series de pérdida y no se
                # podía leer si divergían. Misma fórmula que la de entrenamiento
                # --incluido `ignore_index`-- para que sean comparables.
                val_loss_total += F.cross_entropy(
                    logits.reshape(-1, logits.shape[-1]),
                    labels.reshape(-1),
                    ignore_index=-100,
                ).item()
                val_batches += 1

                preds = logits.argmax(dim=-1)
                n_correct += ((preds == labels) & mask).sum().item()
                n_total += mask.sum().item()

                def_pred = (preds == DEFER_LABEL) & mask
                def_actual = (labels == DEFER_LABEL) & mask
                n_def_pred += def_pred.sum().item()
                n_def_actual += def_actual.sum().item()
                n_def_correct += (def_pred & def_actual).sum().item()

        acc = n_correct / n_total if n_total > 0 else 0.0
        def_prec = n_def_correct / n_def_pred if n_def_pred > 0 else 0.0
        def_rec = n_def_correct / n_def_actual if n_def_actual > 0 else 0.0
        def_f1 = 2 * def_prec * def_rec / (def_prec + def_rec) if (def_prec + def_rec) > 0 else 0.0

        val_loss = val_loss_total / val_batches if val_batches else float("nan")

        train_epochs.append({"loss": train_loss, "acc": train_acc})
        val_metrics.append({"acc": acc, "def_f1": def_f1, "loss": val_loss})

        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(
                f"Epoch {epoch + 1:3d}/{n_epochs}  train_loss={train_loss:.4f}  "
                f"train_acc={train_acc:.4f}  val_loss={val_loss:.4f}  "
                f"val_acc={acc:.4f}  val_def_f1={def_f1:.4f}"
            )

    best_idx = int(np.argmax([m["def_f1"] for m in val_metrics]))
    best = val_metrics[best_idx]
    print(f"\nBest val_def_f1={best['def_f1']:.4f} at epoch {best_idx + 1}")

    # La política del decodificador se elige AQUÍ, antes de cualquier medición
    # con capacidad. Antes se elegía después, y la pasada de abajo usaba
    # `policy="model"` fija: por eso la matriz de confusión del transformer y sus
    # agregados operativos salían de dos decodificadores distintos y no
    # reconciliaban. Una corrida, una política.
    model.eval()
    with torch.no_grad():
        val_logits_by_ep = _episode_logits_batched(model, val_loader, device)
    val_logits = stack_episode_logits(
        val_ds.episodes, val_ds.arrays, _logits_by_index(val_ds.episodes, val_logits_by_ep)
    )
    policy = select_policy(val_ds.episodes, val_ds.arrays, val_logits, len(classes))

    cap_correct = 0
    cap_def_correct = 0
    cap_def_pred = 0
    n_total = 0
    n_def_actual = 0
    cap_labels_all = []
    cap_preds_all = []

    with torch.no_grad():
        for batch in val_loader:
            batch = {
                k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()
            }
            logits = model(batch)
            labels = batch["labels"]
            mask = labels != -100
            cap_preds = predict_with_capacity(
                logits,
                batch["cu"],
                batch["capacities"],
                batch["n_trucks"],
                batch["pad_mask"],
                policy,
            )
            cap_labels_all.append(labels[mask].cpu().numpy())
            cap_preds_all.append(cap_preds[mask].cpu().numpy())
            cap_correct += ((cap_preds == labels) & mask).sum().item()
            n_total += mask.sum().item()
            def_actual = (labels == DEFER_LABEL) & mask
            cap_def = (cap_preds == DEFER_LABEL) & mask
            cap_def_correct += (cap_def & def_actual).sum().item()
            cap_def_pred += cap_def.sum().item()
            n_def_actual += def_actual.sum().item()

    cap_acc = cap_correct / n_total if n_total > 0 else 0.0
    cap_def_prec = cap_def_correct / cap_def_pred if cap_def_pred > 0 else 0.0
    cap_def_rec = cap_def_correct / n_def_actual if n_def_actual > 0 else 0.0
    cap_def_f1 = (
        2 * cap_def_prec * cap_def_rec / (cap_def_prec + cap_def_rec)
        if (cap_def_prec + cap_def_rec) > 0
        else 0.0
    )
    print(f"Capacity-aware (policy={policy}):  val_acc={cap_acc:.4f}  val_def_f1={cap_def_f1:.4f}")

    operational = attention_operational_report(
        model, val_loader, val_ds, device, policy, val_logits
    )

    with mlflow.start_run(run_name=run_name):
        run_id = mlflow.active_run().info.run_id
        mlflow.log_params(
            {
                "att_d_model": d_model,
                "att_nhead": nhead,
                "att_num_layers": num_layers,
                "att_dropout": dropout,
                "att_batch_size": batch_size,
                "att_learning_rate": learning_rate,
                "att_n_epochs": n_epochs,
                "att_seed": seed,
                "att_truck_axis": "dynamic (any T)",
                "att_canonical": "fleet by capacity desc; 0=SIN_CAMION, 1..T",
            }
        )
        # `att_rawargmax_best_*` are DIAGNOSTICS, not publishable figures, and the
        # name now says so. They are a raw argmax -- no capacity decoder -- taken
        # at the epoch that scored best on validation, which is neither the saved
        # weights nor a held-out measurement. The comparison table reads
        # `att_operational.model.*` like every other row.
        mlflow.log_metric("att_rawargmax_best_accuracy", best["acc"])
        mlflow.log_metric("att_rawargmax_best_defer_f1", best["def_f1"])
        mlflow.log_metric("att_rawargmax_best_epoch", best_idx + 1)
        mlflow.log_metric("att_cap_accuracy", cap_acc)
        mlflow.log_metric("att_cap_defer_f1", cap_def_f1)
        mlflow.log_param("att_decoder_policy", policy)

        for epoch, (tm, vm) in enumerate(zip(train_epochs, val_metrics, strict=False), start=1):
            mlflow.log_metric("att_train_loss", tm["loss"], step=epoch)
            mlflow.log_metric("att_val_loss", vm["loss"], step=epoch)
            mlflow.log_metric("att_train_accuracy_curve", tm["acc"], step=epoch)
            mlflow.log_metric("att_val_accuracy_curve", vm["acc"], step=epoch)
            mlflow.log_metric("att_val_defer_f1_curve", vm["def_f1"], step=epoch)

        # Y fuera de MLflow, que es de donde se perdieron. Ver src/modeling/figures.py.
        _guardar_curvas_attention(train_epochs, val_metrics)

        for agg in ("model", "greedy"):
            for k, v in operational[agg].items():
                if isinstance(v, dict):
                    for sub_k, sub_v in v.items():
                        mlflow.log_metric(f"att_{agg}_{k}_{sub_k}", sub_v)
                elif isinstance(v, (int, float, np.integer, np.floating)) and not isinstance(
                    v, bool
                ):
                    mlflow.log_metric(f"att_{agg}_{k}", v)

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "model.pt")
            torch.save(
                _attention_checkpoint(model, classes, ep0, d_model, nhead, num_layers, dropout),
                path,
            )
            mlflow.log_artifact(path, "model")

        _save_attention_artifact(
            model,
            classes,
            ep0,
            train_ds.scaler,
            train_ds.arrays.max_trucks,
            d_model,
            nhead,
            num_layers,
            dropout,
        )

    return {
        "att_results": {
            # Diagnostics of the training loop; see the MLflow block above for why
            # they are named this way and why the table never reads them.
            "att_rawargmax_best_accuracy": best["acc"],
            "att_rawargmax_best_defer_f1": best["def_f1"],
            "att_rawargmax_best_epoch": best_idx + 1,
            "att_cap_accuracy": cap_acc,
            "att_cap_defer_f1": cap_def_f1,
            "att_operational": operational,
            "att_decoder_policy": policy,
            # The comparison table refuses to publish a row that does not declare
            # its split. It used to be exempt because it never carried the key.
            "split_strategy": "time",
            "seed": seed,
            "run_id": run_id,
        },
        "att_predictions": _attention_predictions_df(cap_labels_all, cap_preds_all),
    }


def _guardar_curvas_attention(train_epochs: list[dict], val_metrics: list[dict]) -> None:
    """`training_history.csv` + `learning_curves.png` en artifacts/, versionados.

    Los rótulos salen de `figures.PRESENTACION`, no de aquí: la misma figura la
    puede reescribir `scripts/report_figures.py` al redibujar sin reentrenar, y
    con dos juegos de títulos diría una cosa u otra según quién la escribió.
    """
    from src.modeling.figures import plot_model_curves, write_history

    out_dir = ARTIFACT_ROOT / "attention"
    filas = [
        {
            "loss": tm["loss"],
            "val_loss": vm["loss"],
            "accuracy": tm["acc"],
            "val_accuracy": vm["acc"],
            "val_defer_f1": vm["def_f1"],
        }
        for tm, vm in zip(train_epochs, val_metrics, strict=True)
    ]
    write_history(out_dir / "training_history.csv", filas, "epoch")
    plot_model_curves("attention", filas, "epoch", out_dir)


def _attention_checkpoint(model, classes, ep0, d_model, nhead, num_layers, dropout) -> dict:
    """Serializable state for the pairwise attention model."""
    return {
        "model_state_dict": model.state_dict(),
        "model_config": {
            "vehicle_dim": ep0.vehicle.shape[1],
            "truck_dim": ep0.truck.shape[1],
            "context_dim": len(ep0.context),
            "d_model": d_model,
            "nhead": nhead,
            "num_layers": num_layers,
            "dropout": dropout,
        },
        "classes": classes,
    }


def _save_attention_artifact(
    model, classes, ep0, scaler, max_trucks, d_model, nhead, num_layers, dropout
) -> None:
    """Persist the attention checkpoint + preprocessing schema next to the GBTs."""
    out = ARTIFACT_ROOT / "attention"
    out.mkdir(parents=True, exist_ok=True)
    import json

    torch.save(
        _attention_checkpoint(model, classes, ep0, d_model, nhead, num_layers, dropout),
        out / "model.pt",
    )
    with open(out / "pairwise_schema.json", "w", encoding="utf-8") as fh:
        json.dump(
            {
                "classes": classes,
                "max_trucks_padding": int(max_trucks),
                "blocks": scaler.to_dict(),
                "model_config": _attention_checkpoint(
                    model, classes, ep0, d_model, nhead, num_layers, dropout
                )["model_config"],
            },
            fh,
            indent=2,
            ensure_ascii=False,
        )
