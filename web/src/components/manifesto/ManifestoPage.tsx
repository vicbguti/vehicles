import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { FolderUp, Truck } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ActiveModelBadge } from "@/components/ActiveModelBadge"
import { ApiError, distributeVehicles, validateManifest } from "@/lib/api"
import type { Vehicle } from "@/lib/types"
import { FleetEditor } from "./FleetEditor"
import { UploadManifestoDialog } from "./UploadManifestoDialog"
import { VehicleTable } from "./VehicleTable"

const DEFAULT_FLEET = [6, 6]

export function ManifestoPage() {
  const navigate = useNavigate()
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [fleet, setFleet] = useState<number[]>(DEFAULT_FLEET)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [dialogError, setDialogError] = useState<string | null>(null)
  const [distributing, setDistributing] = useState(false)
  const [distributeError, setDistributeError] = useState<string | null>(null)

  const acceptedCount = vehicles.filter((v) => v.status === "accepted").length

  const handleUpload = async (file: File) => {
    setUploading(true)
    setDialogError(null)
    try {
      const csv = await file.text()
      const validated = await validateManifest(csv, fleet)
      setVehicles(validated)
      setDialogOpen(false)
    } catch (error) {
      setDialogError(error instanceof ApiError ? error.message : "No se pudo procesar el archivo")
    } finally {
      setUploading(false)
    }
  }

  const handleDistribute = async () => {
    setDistributing(true)
    setDistributeError(null)
    try {
      const plan = await distributeVehicles(vehicles, fleet)
      navigate("/distribution", { state: { plan } })
    } catch (error) {
      setDistributeError(error instanceof ApiError ? error.message : "No se pudo generar la distribución")
    } finally {
      setDistributing(false)
    }
  }

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
          <div className="mt-2">
            <ActiveModelBadge />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outline" onClick={() => setVehicles([])} disabled={uploading || distributing}>
            Limpiar
          </Button>
          <Button onClick={() => setDialogOpen(true)} disabled={uploading || distributing}>
            <FolderUp />
            Subir Manifiesto
          </Button>
          <Button
            onClick={handleDistribute}
            disabled={acceptedCount === 0 || distributing || uploading}
          >
            <Truck />
            {distributing ? "Distribuyendo..." : "Obtener Distribución"}
          </Button>
        </div>
      </header>

      {distributeError && (
        <p className="rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
          {distributeError}
        </p>
      )}

      <FleetEditor capacities={fleet} onChange={setFleet} />

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
        loading={uploading}
        error={dialogError}
      />
    </main>
  )
}
