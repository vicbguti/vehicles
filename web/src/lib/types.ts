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
}
