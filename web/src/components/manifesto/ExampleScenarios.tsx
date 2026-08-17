import { FolderDown } from "lucide-react"
import { Button } from "@/components/ui/button"

const SCENARIOS: { name: string; label: string }[] = [
  { name: "profesor", label: "Profesor (18 vehículos)" },
  { name: "profesor-escalado", label: "Profesor-escalado (25)" },
  { name: "real-episode", label: "Caso real (episodio SRI)" },
]

interface ExampleScenariosProps {
  disabled: boolean
  loadingName: string | null
  onLoad: (name: string) => void
}

export function ExampleScenarios({ disabled, loadingName, onLoad }: ExampleScenariosProps) {
  return (
    <section className="flex flex-col gap-3 rounded-lg border border-border p-5">
      <div>
        <h2 className="text-sm font-semibold text-foreground">Casos de ejemplo</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          Cargar un caso completo del API: los vehículos reales del SRI y la flota
          coherente que va con ellos, juntos.
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        {SCENARIOS.map((scenario) => (
          <Button
            key={scenario.name}
            variant="outline"
            onClick={() => onLoad(scenario.name)}
            disabled={disabled || loadingName !== null}
          >
            <FolderDown />
            {loadingName === scenario.name ? "Cargando..." : scenario.label}
          </Button>
        ))}
      </div>
    </section>
  )
}