import { useState } from "react"
import { Plus, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface FleetEditorProps {
  capacities: number[]
  onChange: (capacities: number[]) => void
}

export function FleetEditor({ capacities, onChange }: FleetEditorProps) {
  const [newCapacity, setNewCapacity] = useState("")

  const handleAdd = () => {
    const value = parseFloat(newCapacity)
    if (!Number.isFinite(value) || value <= 0) return
    onChange([...capacities, value])
    setNewCapacity("")
  }

  return (
    <section className="flex flex-col gap-3 rounded-lg border border-border p-5">
      <div>
        <h2 className="text-sm font-semibold text-foreground">Flota de Camiones</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          Define la flota disponible. No hay límite de camiones ni de capacidad.
        </p>
      </div>

      <div className="flex flex-col gap-2">
        {capacities.map((capacity, index) => (
          <div
            key={`${capacity}-${index}`}
            className="flex items-center justify-between rounded-lg border border-border px-3 py-2"
          >
            <span className="text-sm text-foreground">
              Camión {index + 1}
              <span className="ml-2 text-xs text-muted-foreground">
                Capacidad Máxima: {capacity.toFixed(1)}
              </span>
            </span>
            <Button
              variant="ghost"
              size="icon-sm"
              onClick={() => onChange(capacities.filter((_, i) => i !== index))}
              className="size-7 rounded-full bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground"
              aria-label={`Eliminar Camión ${index + 1}`}
            >
              <X />
            </Button>
          </div>
        ))}
      </div>

      <div className="flex items-end gap-2">
        <div className="flex-1">
          <label
            htmlFor="nuevo-camion"
            className="mb-1 block text-xs font-medium text-muted-foreground"
          >
            Capacidad del nuevo camión
          </label>
          <Input
            id="nuevo-camion"
            type="number"
            min="0.1"
            step="0.1"
            value={newCapacity}
            onChange={(e) => setNewCapacity(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
            placeholder="6.0"
          />
        </div>
        <Button variant="outline" onClick={handleAdd} disabled={!newCapacity}>
          <Plus />
          Agregar camión
        </Button>
      </div>
    </section>
  )
}
