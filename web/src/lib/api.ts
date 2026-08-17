import type { DistributionPlan, Health, Scenario, Vehicle } from "@/lib/types"

const BASE_URL = "/api"

const OFFLINE_MESSAGE = "No se pudo conectar con el servidor. Verifica que esté en ejecución."

export class ApiError extends Error {
  constructor(message: string) {
    super(message)
    this.name = "ApiError"
  }
}

async function send<T>(path: string, init: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${BASE_URL}${path}`, init)
  } catch {
    throw new ApiError(OFFLINE_MESSAGE)
  }

  if (!response.ok) {
    let detail = `Error ${response.status}`
    try {
      const payload = await response.json()
      if (typeof payload?.detail === "string") detail = payload.detail
    } catch {
      // Respuesta sin JSON; nos quedamos con el código.
    }
    throw new ApiError(detail)
  }

  return (await response.json()) as T
}

function request<T>(path: string, body: unknown): Promise<T> {
  return send<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })
}

/** Estado del servicio y modelo activo. `FLEET_LOADING_MODEL` se lee al
 * arrancar el servidor, así que este valor sólo cambia si se reinicia. */
export function getHealth(): Promise<Health> {
  return send<Health>("/health", { method: "GET" })
}

/** Un caso completo (vehículos reales + flota coherente) del API.
 *  El servidor responde en snake_case; aquí se mapea a camelCase, como hace
 *  ``distributeVehicles`` con ``sin_camion``/``elapsed_ms``. */
export async function getScenario(name: string): Promise<Scenario> {
  const payload = await send<{
    name: string
    fleet: number[]
    vehicles_count: number
    csv_url: string
    iso_year?: number
    iso_week?: number
    canton?: string
  }>(`/scenarios/${name}`, { method: "GET" })
  return {
    name: payload.name,
    fleet: payload.fleet,
    vehiclesCount: payload.vehicles_count,
    csvUrl: payload.csv_url,
    isoYear: payload.iso_year,
    isoWeek: payload.iso_week,
    canton: payload.canton,
  }
}

/** El CSV del caso (``Scenario.csvUrl``), como texto para ``validateManifest``. */
export async function getManifestCsv(csvUrl: string): Promise<string> {
  let response: Response
  try {
    response = await fetch(csvUrl)
  } catch {
    throw new ApiError(OFFLINE_MESSAGE)
  }
  if (!response.ok) throw new ApiError(`Error ${response.status} al descargar el manifiesto`)
  return response.text()
}

export async function validateManifest(csv: string, fleet: number[]): Promise<Vehicle[]> {
  const payload = await request<{ vehicles: Vehicle[] }>("/manifest", { csv, fleet })
  return payload.vehicles
}

export async function distributeVehicles(
  vehicles: Vehicle[],
  fleet: number[],
): Promise<DistributionPlan> {
  const accepted = vehicles
    .filter((v) => v.status === "accepted")
    .map((v) => ({
      identificador: v.identificador,
      clase: v.clase,
      cu: v.cu,
      canton: v.canton,
    }))
  const startedAt = performance.now()
  const payload = await request<{
    trucks: DistributionPlan["trucks"]
    sin_camion: { vehicles: Vehicle[] }
    model: string
    elapsed_ms: number
  }>("/distribute", {
    vehicles: accepted,
    fleet,
  })
  return {
    trucks: payload.trucks,
    sinCamion: payload.sin_camion.vehicles,
    model: payload.model,
    elapsedMs: payload.elapsed_ms,
    roundTripMs: performance.now() - startedAt,
    vehicleCount: accepted.length,
  }
}
