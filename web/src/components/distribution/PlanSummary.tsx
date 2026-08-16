import { Cpu, Gauge, Timer, Truck } from "lucide-react"
import type { LucideIcon } from "lucide-react"
import { formatDuration, modelLabel } from "@/lib/models"
import type { DistributionPlan } from "@/lib/types"

interface StatProps {
  icon: LucideIcon
  label: string
  value: string
  hint: string
}

function Stat({ icon: Icon, label, value, hint }: StatProps) {
  return (
    <div className="flex flex-col gap-1 rounded-lg border border-border px-4 py-3">
      <span className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
        <Icon className="size-3.5" />
        {label}
      </span>
      <span className="text-lg font-semibold leading-tight text-foreground">{value}</span>
      <span className="text-xs text-muted-foreground">{hint}</span>
    </div>
  )
}

/**
 * Qué modelo resolvió el plan y cuánto tardó.
 *
 * Se muestran dos tiempos porque miden cosas distintas: `elapsedMs` es el
 * trabajo del modelo en el servidor —lo comparable entre los seis— y
 * `roundTripMs` es lo que esperó el navegador, que además incluye la red y el
 * serializado. El recuento de vehículos va al lado porque un tiempo sin saber
 * sobre cuántos vehículos se midió no dice nada.
 */
export function PlanSummary({ plan }: { plan: DistributionPlan }) {
  const loaded = plan.trucks.reduce((total, truck) => total + truck.vehicles.length, 0)
  const perVehicle = plan.vehicleCount > 0 ? plan.elapsedMs / plan.vehicleCount : 0

  return (
    <div className="flex flex-col gap-2">
      <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat
          icon={Cpu}
          label="Modelo"
          value={modelLabel(plan.model)}
          hint="Fijado con FLEET_LOADING_MODEL"
        />
        <Stat
          icon={Timer}
          label="Tiempo del modelo"
          value={formatDuration(plan.elapsedMs)}
          hint={`${formatDuration(perVehicle)} por vehículo`}
        />
        <Stat
          icon={Gauge}
          label="Ida y vuelta"
          value={formatDuration(plan.roundTripMs)}
          hint="Incluye red y serialización"
        />
        <Stat
          icon={Truck}
          label="Vehículos asignados"
          value={`${loaded} de ${plan.vehicleCount}`}
          hint={`En ${plan.trucks.length} ${plan.trucks.length === 1 ? "camión" : "camiones"}`}
        />
      </section>
      <p className="text-xs text-muted-foreground">
        La primera distribución tras arrancar el servidor incluye el calentamiento del modelo y
        puede tardar bastante más. Para comparar modelos entre sí, usa una repetición posterior.
      </p>
    </div>
  )
}
