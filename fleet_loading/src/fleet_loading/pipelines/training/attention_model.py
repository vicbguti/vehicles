from __future__ import annotations

import math
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

from fleet_loading.pipelines.training.operational import (
    DEFERRED,
    aggregate_operational,
    episode_report,
    greedy_report,
)

TRUCK_NAMES = ["CAMION_1", "CAMION_2", "CAMION_3", "CAMION_4"]
DEFER_LABEL = 4  # index for SIN_CAMION
MAX_TRUCKS = 4


def encode_target(truck_series: pd.Series, n_trucks: int) -> np.ndarray:
    labels = np.full(len(truck_series), DEFER_LABEL, dtype=np.int64)
    for i, name in enumerate(TRUCK_NAMES[:n_trucks]):
        mask = truck_series.values == name
        labels[mask] = i
    return labels


class EpisodeDataset(Dataset):
    def __init__(self, df: pd.DataFrame, episodes: pd.DataFrame):
        self.df = df
        self.episodes = episodes.set_index("episode_id")

        self.canton_codes, _ = pd.factorize(df["canton"])
        self.clase_codes, _ = pd.factorize(df["clase"])
        self.n_canton = int(self.canton_codes.max() + 1)
        self.n_clase = int(self.clase_codes.max() + 1)

        self.episode_ids = df["episode_id"].unique()
        self.episode_indices = df.groupby("episode_id").indices

    def __len__(self):
        return len(self.episode_ids)

    def __getitem__(self, idx):
        ep_id = self.episode_ids[idx]
        indices = self.episode_indices[ep_id]
        group = self.df.iloc[indices]
        ep_row = self.episodes.loc[ep_id]

        n = len(group)
        cu = group["cu"].values.astype(np.float32)
        canton = self.canton_codes[indices].astype(np.int64)
        clase = self.clase_codes[indices].astype(np.int64)

        iso_week = float(ep_row["iso_week"])
        iso_week_sin = math.sin(2 * math.pi * iso_week / 52)
        iso_week_cos = math.cos(2 * math.pi * iso_week / 52)
        n_vehicles = float(n)
        n_trucks = int(ep_row["n_trucks"])
        total_cu = float(cu.sum())
        total_capacity = float(sum(ep_row["truck_capacities"]))

        episode_feats = np.array(
            [iso_week_sin, iso_week_cos, n_vehicles, n_trucks, total_cu, total_capacity],
            dtype=np.float32,
        )

        labels = encode_target(group["truck"], n_trucks)

        # mask for trucks that don't exist in this episode
        label_mask = np.ones(MAX_TRUCKS + 1, dtype=bool)
        label_mask[n_trucks] = False  # defer always valid
        label_mask[:n_trucks] = False

        return {
            "cu": cu,
            "canton": canton,
            "clase": clase,
            "episode_feats": episode_feats,
            "labels": labels,
            "label_mask": label_mask,
            "n": n,
            "n_trucks": n_trucks,
            "capacities": np.array(ep_row["truck_capacities"], dtype=np.float32),
        }


def collate_episodes(batch):
    max_n = max(item["n"] for item in batch)
    n_feats = len(batch[0]["episode_feats"])
    n_eps = len(batch)

    cu = torch.zeros(n_eps, max_n)
    canton = torch.zeros(n_eps, max_n, dtype=torch.long)
    clase = torch.zeros(n_eps, max_n, dtype=torch.long)
    labels = torch.full((n_eps, max_n), -100, dtype=torch.long)
    episode_feats = torch.zeros(n_eps, n_feats)
    label_mask = torch.zeros(n_eps, MAX_TRUCKS + 1, dtype=torch.bool)
    pad_mask = torch.ones(n_eps, max_n, dtype=torch.bool)

    for i, item in enumerate(batch):
        n = item["n"]
        cu[i, :n] = torch.from_numpy(item["cu"])
        canton[i, :n] = torch.from_numpy(item["canton"])
        clase[i, :n] = torch.from_numpy(item["clase"])
        labels[i, :n] = torch.from_numpy(item["labels"])
        episode_feats[i] = torch.from_numpy(item["episode_feats"])
        label_mask[i] = torch.from_numpy(item["label_mask"])
        pad_mask[i, :n] = False

    capacities = torch.zeros(n_eps, MAX_TRUCKS)
    n_trucks_arr = torch.zeros(n_eps, dtype=torch.long)

    for i, item in enumerate(batch):
        n = item["n"]
        capacities[i, :item["n_trucks"]] = torch.from_numpy(item["capacities"])
        n_trucks_arr[i] = item["n_trucks"]

    return {
        "cu": cu,
        "canton": canton,
        "clase": clase,
        "episode_feats": episode_feats,
        "labels": labels,
        "label_mask": label_mask,
        "pad_mask": pad_mask,
        "capacities": capacities,
        "n_trucks": n_trucks_arr,
    }


class AttentionModel(nn.Module):
    def __init__(
        self,
        n_canton: int,
        n_clase: int,
        d_model: int = 64,
        nhead: int = 4,
        num_layers: int = 3,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.d_model = d_model
        self.canton_embed = nn.Embedding(n_canton, d_model // 4)
        self.clase_embed = nn.Embedding(n_clase, d_model // 4)
        self.cu_proj = nn.Linear(1, d_model // 4)
        self.episode_proj = nn.Linear(6, d_model)

        self.vehicle_dim = (d_model // 4) * 3
        self.input_proj = nn.Linear(self.vehicle_dim, d_model)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        self.output_head = nn.Linear(d_model, MAX_TRUCKS + 1)

    def forward(self, batch):
        cu = batch["cu"].unsqueeze(-1)
        canton = batch["canton"]
        clase = batch["clase"]
        episode_feats = batch["episode_feats"]
        pad_mask = batch["pad_mask"]

        cu_emb = self.cu_proj(cu)
        canton_emb = self.canton_embed(canton)
        clase_emb = self.clase_embed(clase)

        ep_emb = self.episode_proj(episode_feats).unsqueeze(1)
        vehicle_emb = torch.cat([cu_emb, canton_emb, clase_emb], dim=-1)
        vehicle_emb = self.input_proj(vehicle_emb)

        vehicle_emb = vehicle_emb + ep_emb

        out = self.transformer(vehicle_emb, src_key_padding_mask=pad_mask)
        logits = self.output_head(out)
        return logits


@torch.no_grad()
def predict_with_capacity(
    logits: torch.Tensor,
    cu: torch.Tensor,
    capacities: torch.Tensor,
    n_trucks_arr: torch.Tensor,
    pad_mask: torch.Tensor,
) -> torch.Tensor:
    batch_size, max_n, _ = logits.shape
    preds = torch.full((batch_size, max_n), DEFER_LABEL, dtype=torch.long, device=logits.device)

    for b in range(batch_size):
        n = max_n - pad_mask[b].sum().item()
        remaining = capacities[b].clone()
        n_trucks = int(n_trucks_arr[b].item())

        cu_order = torch.argsort(cu[b, :n], descending=True)

        for idx in cu_order:
            vehicle_cu = cu[b, idx].item()
            truck_logits = logits[b, idx, :n_trucks]
            valid = remaining[:n_trucks] >= vehicle_cu
            if valid.any():
                masked = truck_logits.clone()
                masked[~valid] = -float("inf")
                chosen = masked.argmax().item()
                preds[b, idx] = chosen
                remaining[chosen] -= vehicle_cu
            else:
                preds[b, idx] = DEFER_LABEL

    return preds


def attention_operational_report(
    model: nn.Module,
    val_loader: DataLoader,
    val_ds: EpisodeDataset,
    episodes: pd.DataFrame,
    device,
) -> dict:
    """Capacity-aware operational report for the attention model vs teacher."""
    ep = episodes.set_index("episode_id")
    rows: list[dict] = []
    latency: list[float] = []

    model.eval()
    with torch.no_grad():
        for ep_ids in _episode_id_chunks(val_ds, val_loader.batch_size):
            batch = None  # placeholder; reassigned below
        for batch in val_loader:
            pass
    raise NotImplementedError


def attention_operational_report(
    model: nn.Module,
    val_loader: DataLoader,
    val_ds: EpisodeDataset,
    episodes: pd.DataFrame,
    device,
) -> dict:
    """Capacity-aware operational report for the attention model vs teacher."""
    ep = episodes.set_index("episode_id")
    rows: list[dict] = []
    latency: list[float] = []

    model.eval()
    cursor = 0
    with torch.no_grad():
        for batch in val_loader:
            batch = {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}
            logits = model(batch)
            t0 = time.perf_counter()
            cap_preds = predict_with_capacity(
                logits, batch["cu"], batch["capacities"],
                batch["n_trucks"], batch["pad_mask"],
            )
            latency_ms = (time.perf_counter() - t0) * 1000.0

            n_eps = batch["cu"].shape[0]
            for i in range(n_eps):
                ep_id = val_ds.episode_ids[cursor + i]
                n = int((batch["labels"][i] != -100).sum().item())
                caps = np.asarray(ep.loc[ep_id, "truck_capacities"], dtype=float)
                cu = batch["cu"][i, :n].cpu().numpy().astype(float)
                teacher_n = int(ep.loc[ep_id, "n_loaded"])
                teacher_cu = float(ep.loc[ep_id, "cu_utilized"])

                assign = cap_preds[i, :n].cpu().numpy().astype(int)
                assign = np.where(assign == DEFER_LABEL, DEFERRED, assign)

                rows.append(
                    episode_report(ep_id, assign, cu, caps, teacher_n, teacher_cu)
                )
                latency.append(latency_ms / n_eps)

            cursor += n_eps

    return {
        "model": aggregate_operational(rows, latency),
        "greedy": aggregate_operational(*greedy_report(val_ds.df, episodes)),
    }


def _attention_predictions_df(cap_labels_all, cap_preds_all) -> pd.DataFrame:
    """Combine capacity-aware val predictions into a DataFrame for the report node."""
    return pd.DataFrame({
        "y_true": np.concatenate(cap_labels_all),
        "y_pred": np.concatenate(cap_preds_all),
    })


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
    run_name: str,
) -> dict:
    import warnings
    warnings.filterwarnings("ignore")

    train_ds = EpisodeDataset(train_df, episodes)
    val_ds = EpisodeDataset(val_df, episodes)

    train_loader = DataLoader(
        train_ds, batch_size=batch_size, shuffle=True, collate_fn=collate_episodes
    )
    val_loader = DataLoader(
        val_ds, batch_size=batch_size, shuffle=False, collate_fn=collate_episodes
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = AttentionModel(
        n_canton=train_ds.n_canton,
        n_clase=train_ds.n_clase,
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
            batch = {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}
            logits = model(batch)

            labels = batch["labels"]
            loss = F.cross_entropy(
                logits.reshape(-1, MAX_TRUCKS + 1),
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

        with torch.no_grad():
            for batch in val_loader:
                batch = {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}
                logits = model(batch)

                labels = batch["labels"]
                mask = labels != -100

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

        train_epochs.append({"loss": train_loss, "acc": train_acc})
        val_metrics.append({"acc": acc, "def_f1": def_f1})

        if (epoch + 1) % 10 == 0 or epoch == 0:
            print(f"Epoch {epoch+1:3d}/{n_epochs}  train_loss={train_loss:.4f}  train_acc={train_acc:.4f}  val_acc={acc:.4f}  val_def_f1={def_f1:.4f}")

    best_idx = int(np.argmax([m["def_f1"] for m in val_metrics]))
    best = val_metrics[best_idx]
    print(f"\nBest val_def_f1={best['def_f1']:.4f} at epoch {best_idx+1}")

    # Evaluate best model with capacity masking
    best_ckpt = {k: v for k, v in model.state_dict().items()}
    model.load_state_dict(best_ckpt)

    model.eval()
    cap_correct = 0
    cap_def_correct = 0
    cap_def_pred = 0
    n_total = 0
    n_def_actual = 0
    cap_labels_all = []
    cap_preds_all = []

    with torch.no_grad():
        for batch in val_loader:
            batch = {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in batch.items()}
            logits = model(batch)
            labels = batch["labels"]
            mask = labels != -100
            cap_preds = predict_with_capacity(
                logits, batch["cu"], batch["capacities"],
                batch["n_trucks"], batch["pad_mask"],
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
    cap_def_f1 = 2 * cap_def_prec * cap_def_rec / (cap_def_prec + cap_def_rec) if (cap_def_prec + cap_def_rec) > 0 else 0.0
    print(f"Capacity-aware:   val_acc={cap_acc:.4f}  val_def_f1={cap_def_f1:.4f}")

    import mlflow
    import tempfile
    import os

    operational = attention_operational_report(
        model, val_loader, val_ds, episodes, device
    )

    with mlflow.start_run(run_name=run_name):
        run_id = mlflow.active_run().info.run_id
        mlflow.log_params({
            "att_d_model": d_model,
            "att_nhead": nhead,
            "att_num_layers": num_layers,
            "att_dropout": dropout,
            "att_batch_size": batch_size,
            "att_learning_rate": learning_rate,
            "att_n_epochs": n_epochs,
            "att_n_canton": train_ds.n_canton,
            "att_n_clase": train_ds.n_clase,
        })
        mlflow.log_metric("att_val_accuracy", best["acc"])
        mlflow.log_metric("att_val_defer_f1", best["def_f1"])
        mlflow.log_metric("att_cap_accuracy", cap_acc)
        mlflow.log_metric("att_cap_defer_f1", cap_def_f1)

        for epoch, (tm, vm) in enumerate(zip(train_epochs, val_metrics), start=1):
            mlflow.log_metric("att_train_loss", tm["loss"], step=epoch)
            mlflow.log_metric("att_train_accuracy_curve", tm["acc"], step=epoch)
            mlflow.log_metric("att_val_accuracy_curve", vm["acc"], step=epoch)
            mlflow.log_metric("att_val_defer_f1_curve", vm["def_f1"], step=epoch)

        for agg in ("model", "greedy"):
            for k, v in operational[agg].items():
                if isinstance(v, dict):
                    for sub_k, sub_v in v.items():
                        mlflow.log_metric(f"att_{agg}_{k}_{sub_k}", sub_v)
                else:
                    mlflow.log_metric(f"att_{agg}_{k}", v)

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "model.pt")
            torch.save({"model_state_dict": model.state_dict(), "n_canton": train_ds.n_canton, "n_clase": train_ds.n_clase}, path)
            mlflow.log_artifact(path, "model")

    return {
        "att_results": {
            "att_val_accuracy": best["acc"],
            "att_val_defer_f1": best["def_f1"],
            "att_cap_accuracy": cap_acc,
            "att_cap_defer_f1": cap_def_f1,
            "att_operational": operational,
            "run_id": run_id,
        },
        "att_predictions": _attention_predictions_df(cap_labels_all, cap_preds_all),
    }