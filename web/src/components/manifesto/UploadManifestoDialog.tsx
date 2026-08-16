import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { FileDropzone } from "./FileDropzone"
import { SelectedFile } from "./SelectedFile"

interface UploadManifestoDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onContinue: (file: File) => void
  loading?: boolean
  error?: string | null
}

export function UploadManifestoDialog({
  open,
  onOpenChange,
  onContinue,
  loading = false,
  error = null,
}: UploadManifestoDialogProps) {
  const [file, setFile] = useState<File | null>(null)

  const handleOpenChange = (next: boolean) => {
    if (!next && !loading) setFile(null)
    onOpenChange(next)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="text-lg">Subir Manifiesto de Transporte</DialogTitle>
          <DialogDescription>
            Agrega el archivo del manifiesto de vehículos a transportar aquí
          </DialogDescription>
        </DialogHeader>

        <FileDropzone
          onFileSelect={(f) => {
            if (f.name.toLowerCase().endsWith(".csv")) setFile(f)
          }}
        />

        <p className="text-xs text-muted-foreground">Sólo soporta archivos .csv</p>

        {file && <SelectedFile file={file} onRemove={() => setFile(null)} />}

        {error && (
          <p className="rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)} disabled={loading}>
            Cancelar
          </Button>
          <Button
            disabled={!file || loading}
            onClick={() => file && onContinue(file)}
          >
            {loading ? "Validando..." : "Continuar"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
