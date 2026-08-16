import type { DistributionPlan, Vehicle } from "@/lib/types"

const BASE_URL = "/api"

export class ApiError extends Error {
  constructor(message: string) {
    super(message)
    this.name = "ApiError"
  }
}

async function request<T>(path: string, body: unknown): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
  } catch {
    throw new ApiError("No se pudo conectar con el servidor. Verifica que esté en ejecución.")
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
  const payload = await request<DistributionPlan>("/distribute", {
    vehicles: accepted,
    fleet,
  })
  return payload
}
