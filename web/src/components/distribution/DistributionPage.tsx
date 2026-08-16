import { useState } from "react"
import { useLocation, useNavigate } from "react-router-dom"
import { ArrowLeft, Truck } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import type { DistributionPlan, Truck as TruckPlan } from "@/lib/types"
import { TruckSection } from "./TruckSection"
import { DistributionTable } from "./DistributionTable"
import { PlanSummary } from "./PlanSummary"

export function DistributionPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const plan = (location.state?.plan ?? null) as DistributionPlan | null

  const [trucks, setTrucks] = useState<TruckPlan[] | null>(plan?.trucks ?? null)
  const sinCamion = plan?.sinCamion ?? []

  const handleRemoveTruck = (id: string) =>
    setTrucks((prev) => (prev ? prev.filter((t) => t.id !== id) : prev))

  if (!trucks) {
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
        <section className="flex flex-col items-center gap-3 py-16 text-center">
          <Truck className="size-10 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            Aún no hay un plan. Obtén la distribución desde el manifiesto.
          </p>
          <Button onClick={() => navigate("/")} variant="outline">
            Ir al manifiesto
          </Button>
        </section>
      </main>
    )
  }

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

      {plan && <PlanSummary plan={{ ...plan, trucks }} />}

      {trucks.map((truck, index) => (
        <div key={truck.id} className="flex flex-col gap-8">
          {index > 0 && <Separator />}
          <TruckSection
            truck={truck}
            onRemove={() => handleRemoveTruck(truck.id)}
          />
        </div>
      ))}

      {sinCamion.length > 0 && (
        <>
          <Separator />
          <section className="flex flex-col gap-3">
            <h2 className="text-base font-semibold text-foreground">
              Sin Camión
              <span className="ml-1 font-normal text-muted-foreground">
                ({sinCamion.length} vehículos sin espacio disponible)
              </span>
            </h2>
            <DistributionTable vehicles={sinCamion} />
          </section>
        </>
      )}
    </main>
  )
}
