/**
 * Nombres presentables de los seis modelos que sirve el API y formato de los
 * tiempos que devuelve. El identificador crudo es el valor de
 * `FLEET_LOADING_MODEL`; aquí sólo se traduce para mostrarlo.
 */

const MODEL_LABELS: Record<string, string> = {
  xgboost: "XGBoost",
  lightgbm: "LightGBM",
  attention: "Transformer",
  mlp: "MLP (Keras)",
  rf: "Random Forest",
  logreg: "Regresión logística",
}

/** Etiqueta legible del modelo; si el API reporta uno desconocido, se muestra tal cual. */
export function modelLabel(model: string): string {
  return MODEL_LABELS[model] ?? model
}

/**
 * Milisegundos en una escala legible: bajo un segundo se muestran enteros,
 * por encima en segundos con dos decimales.
 */
export function formatDuration(ms: number): string {
  if (!Number.isFinite(ms) || ms < 0) return "-"
  if (ms < 1) return "<1 ms"
  if (ms < 1000) return `${Math.round(ms)} ms`
  return `${(ms / 1000).toFixed(2)} s`
}
