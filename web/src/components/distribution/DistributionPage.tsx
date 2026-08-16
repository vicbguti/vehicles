import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { initialDistribution } from "@/data/distribution"
import type { DistributionGroup } from "@/lib/types"
import { TruckSection } from "./TruckSection"

export function DistributionPage() {
  const navigate = useNavigate()
  const [groups, setGroups] = useState<DistributionGroup[]>(initialDistribution)

  return (
    <main className="mx-auto flex max-w-[1200px] flex-col gap-8 px-8 py-8">
      <header className="flex flex-col gap-2">
        <Button
          variant="ghost"
          onClick={() => navigate("/")}
          className="self-start px-0 text-muted-foreground hover:bg-transparent hover:text-foreground"
        >
          <ArrowLeft />
          Volver al manifiesto
        </Button>
        <p className="text-xs font-medium uppercase tracking-widest text-muted-foreground">
          Plan de
        </p>
        <h1 className="text-3xl font-semibold tracking-tight text-foreground">Distribución</h1>
      </header>

      {groups.map((group, index) => (
        <div key={group.id} className="flex flex-col gap-8">
          {index > 0 && <Separator />}
          <TruckSection
            group={group}
            onRemove={
              group.name === "Sin Camión"
                ? undefined
                : () => setGroups((prev) => prev.filter((g) => g.id !== group.id))
            }
          />
        </div>
      ))}
    </main>
  )
}
