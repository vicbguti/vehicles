export type VehicleStatus = "accepted" | "rejected"

export interface Vehicle {
  identificador: string
  clase: string
  cu: number
  canton: string
  status: VehicleStatus
  reason?: string
}

export interface Truck {
  id: string
  capacity: number
  vehicles: Vehicle[]
}

export interface DistributionPlan {
  trucks: Truck[]
  sinCamion: Vehicle[]
  /** Modelo que resolvió el plan, tal y como lo reporta el servidor. */
  model: string
  /** Milisegundos de inferencia + decodificación, medidos en el servidor. */
  elapsedMs: number
  /** Milisegundos de ida y vuelta completos, medidos en el navegador. */
  roundTripMs: number
  /** Cuántos vehículos aceptados se enviaron a distribuir. */
  vehicleCount: number
}

export interface Health {
  status: string
  model: string
}

/** Un caso completo servido por el API: los vehículos reales y la flota que
 *  va con ellos, para que la UI los cargue juntos. */
export interface Scenario {
  name: string
  fleet: number[]
  vehiclesCount: number
  csvUrl: string
  isoYear?: number
  isoWeek?: number
  canton?: string
}
