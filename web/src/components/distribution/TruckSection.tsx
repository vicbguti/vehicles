import { X } from "lucide-react"
import { Button } from "@/components/ui/button"
import type { DistributionGroup } from "@/lib/types"
import { DistributionTable } from "./DistributionTable"

interface TruckSectionProps {
  group: DistributionGroup
  onRemove?: () => void
}

export function TruckSection({ group, onRemove }: TruckSectionProps) {
  return (
    <section className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-foreground">
          {group.name}
          {group.capacity !== undefined && (
            <span className="ml-1 font-normal text-muted-foreground">
              (Capacidad Máxima: {group.capacity.toFixed(1)} Unidades de Almacenamiento)
            </span>
          )}
        </h2>
        {onRemove && (
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={onRemove}
            className="text-muted-foreground hover:text-foreground"
            aria-label={`Eliminar ${group.name}`}
          >
            <X />
          </Button>
        )}
      </div>
      <DistributionTable vehicles={group.vehicles} />
    </section>
  )
}
