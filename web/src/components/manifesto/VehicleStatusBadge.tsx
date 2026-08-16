import { Badge } from "@/components/ui/badge"
import type { Vehicle } from "@/lib/types"

export function VehicleStatusBadge({ vehicle }: { vehicle: Vehicle }) {
  if (vehicle.status === "accepted") {
    return (
      <Badge className="bg-emerald-50 text-emerald-700" variant="outline">
        Aceptado
      </Badge>
    )
  }

  return (
    <Badge className="bg-zinc-100 text-zinc-600" variant="outline">
      Rechazado{vehicle.reason ? ` (${vehicle.reason})` : ""}
    </Badge>
  )
}
