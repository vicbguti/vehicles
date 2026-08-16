import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { FolderUp, Truck } from "lucide-react"
import { Button } from "@/components/ui/button"
import { initialVehicles } from "@/data/vehicles"
import type { Vehicle } from "@/lib/types"
import { VehicleTable } from "./VehicleTable"
import { UploadManifestoDialog } from "./UploadManifestoDialog"

export function ManifestoPage() {
  const navigate = useNavigate()
  const [vehicles, setVehicles] = useState<Vehicle[]>(initialVehicles)
  const [dialogOpen, setDialogOpen] = useState(false)

  const handleClear = () => setVehicles([])
  const handleUpload = () => setVehicles(initialVehicles)

  return (
    <main className="mx-auto flex max-w-[1200px] flex-col gap-8 px-8 py-8">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Manifesto de Transporte
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manifiesto de vehículos a transportar
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outline" onClick={handleClear}>
            Limpiar
          </Button>
          <Button onClick={() => setDialogOpen(true)}>
            <FolderUp />
            Subir Manifiesto
          </Button>
          <Button onClick={() => navigate("/distribution")}>
            <Truck />
            Obtener Distribución
          </Button>
        </div>
      </header>

      <section className="rounded-lg border border-border">
        {vehicles.length === 0 ? (
          <p className="py-16 text-center text-sm text-muted-foreground">
            No hay vehículos cargados. Sube un manifiesto para comenzar.
          </p>
        ) : (
          <VehicleTable vehicles={vehicles} />
        )}
      </section>

      <UploadManifestoDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onContinue={handleUpload}
      />
    </main>
  )
}
