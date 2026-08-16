import type { DistributionPlan, Health, Vehicle } from "@/lib/types"

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
