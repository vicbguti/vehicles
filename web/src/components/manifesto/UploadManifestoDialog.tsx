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
  onContinue: () => void
}

export function UploadManifestoDialog({
  open,
  onOpenChange,
  onContinue,
}: UploadManifestoDialogProps) {
  const [file, setFile] = useState<File | null>(null)

  const handleOpenChange = (next: boolean) => {
    if (!next) setFile(null)
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

        <DialogFooter>
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            Cancelar
          </Button>
          <Button
            disabled={!file}
            onClick={() => {
              handleOpenChange(false)
              onContinue()
            }}
          >
            Continuar
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
