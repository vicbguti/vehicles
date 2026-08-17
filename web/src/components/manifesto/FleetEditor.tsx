import { useState } from "react"
import { ChevronDown, ChevronUp, Plus, X } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface FleetEditorProps {
  capacities: number[]
  onChange: (capacities: number[]) => void
}

const PRESETS: { label: string; capacities: number[] }[] = [
  { label: "Profesor (6,6)", capacities: [6, 6] },
  { label: "Profesor-escalado (6,7,7)", capacities: [6, 7, 7] },
]

// Por debajo de este número la lista se muestra entera; por encima, se pliega
// a un resumen para no tapar la tabla de vehículos (un caso real puede traer
// cientos de camiones).
const MAX_VISIBLE_TRUCKS = 10

export function FleetEditor({ capacities, onChange }: FleetEditorProps) {
  const [newCapacity, setNewCapacity] = useState("")
  const [bulkText, setBulkText] = useState(capacities.join(", "))
  const [bulkError, setBulkError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState(false)

  const total = capacities.reduce((sum, capacity) => sum + capacity, 0)
  const isLong = capacities.length > MAX_VISIBLE_TRUCKS
  const showList = !isLong || expanded

  const handleAdd = () => {
    const value = parseFloat(newCapacity)
    if (!Number.isFinite(value) || value <= 0) return
    onChange([...capacities, value])
    setNewCapacity("")
  }

  const parseBulk = (text: string): number[] | null => {
    const parsed = text
      .split(",")
      .map((part) => parseFloat(part.trim()))
      .filter((value) => Number.isFinite(value))
    if (parsed.length === 0 || parsed.some((value) => value <= 0)) return null
    return parsed
  }

  const applyBulk = () => {
    const parsed = parseBulk(bulkText)
    if (parsed === null) {
      setBulkError("Escribe capacidades separadas por coma, todas mayores a 0 (p. ej. 6,6).")
      return
    }
    setBulkError(null)
    onChange(parsed)
  }

  const applyPreset = (preset: { label: string; capacities: number[] }) => {
    setBulkError(null)
    setBulkText(preset.capacities.join(", "))
    onChange(preset.capacities)
  }

  return (
    <section className="flex flex-col gap-3 rounded-lg border border-border p-5">
      <div>
        <h2 className="text-sm font-semibold text-foreground">Flota de Camiones</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          Define la flota disponible. No hay límite de camiones ni de capacidad.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {PRESETS.map((preset) => (
          <Badge
            key={preset.label}
            variant="outline"
            className="cursor-pointer"
            onClick={() => applyPreset(preset)}
          >
            {preset.label}
          </Badge>
        ))}
      </div>

      <div className="flex items-end gap-2">
        <div className="flex-1">
          <label
            htmlFor="flota-csv"
            className="mb-1 block text-xs font-medium text-muted-foreground"
          >
            Capacidades separadas por coma (como el CSV)
          </label>
          <Input
            id="flota-csv"
            value={bulkText}
            onChange={(e) => {
              setBulkText(e.target.value)
              setBulkError(null)
            }}
            onKeyDown={(e) => e.key === "Enter" && applyBulk()}
            placeholder="6,6"
          />
          {bulkError && (
            <p className="mt-1 text-xs text-destructive">{bulkError}</p>
          )}
        </div>
        <Button variant="outline" onClick={applyBulk}>
          Aplicar flota
        </Button>
      </div>

      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground">
          {capacities.length} camiones · capacidad total {total.toFixed(1)}
        </span>
        {isLong && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setExpanded((value) => !value)}
            className="text-xs text-muted-foreground hover:text-foreground"
          >
            {expanded ? (
              <>
                <ChevronUp /> Ocultar lista
              </>
            ) : (
              <>
                <ChevronDown /> Ver lista completa
              </>
            )}
          </Button>
        )}
      </div>

      {showList && (
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
      )}

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
