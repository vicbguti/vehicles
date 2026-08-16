export type VehicleStatus = "accepted" | "rejected"

export interface Vehicle {
  id: string
  clase: string
  storage: string
  canton: string
  status: VehicleStatus
  reason?: string
}

export interface DistributionGroup {
  id: string
  name: string
  capacity?: number
  vehicles: Vehicle[]
}
