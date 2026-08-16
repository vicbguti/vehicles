import { X } from "lucide-react"
import { Button } from "@/components/ui/button"
import type { Truck } from "@/lib/types"
import { DistributionTable } from "./DistributionTable"

interface TruckSectionProps {
  truck: Truck
  onRemove?: () => void
}

export function TruckSection({ truck, onRemove }: TruckSectionProps) {
  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-foreground">
          {truck.id}
          <span className="ml-1 font-normal text-muted-foreground">
            (Capacidad Máxima: {truck.capacity.toFixed(1)} Unidades de Almacenamiento)
          </span>
        </h2>
        {onRemove && (
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={onRemove}
            className="text-muted-foreground hover:text-foreground"
            aria-label={`Eliminar ${truck.id}`}
          >
            <X />
          </Button>
        )}
      </div>
      <DistributionTable vehicles={truck.vehicles} />
    </section>
  )
}
