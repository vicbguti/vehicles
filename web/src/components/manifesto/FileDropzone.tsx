import { useRef, useState } from "react"
import { FileUp, Upload } from "lucide-react"
import { Button } from "@/components/ui/button"

interface FileDropzoneProps {
  onFileSelect: (file: File) => void
}

export function FileDropzone({ onFileSelect }: FileDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)

  const handleFiles = (files: FileList | null) => {
    const file = files?.[0]
    if (file) onFileSelect(file)
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault()
        setIsDragging(true)
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(e) => {
        e.preventDefault()
        setIsDragging(false)
        handleFiles(e.dataTransfer.files)
      }}
      className={`flex h-56 flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-6 transition-colors ${
        isDragging ? "border-primary bg-primary/5" : "border-primary/60"
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv"
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />

      <div className="flex size-12 items-center justify-center rounded-full bg-primary/10">
        <FileUp className="size-6 text-primary" />
      </div>

      <p className="text-center text-sm font-medium text-foreground">
        Arrastra el archivo aquí para empezar a subir
      </p>

      <div className="flex w-full items-center gap-3 text-xs text-muted-foreground">
        <div className="h-px flex-1 bg-border" />
        <span>o</span>
        <div className="h-px flex-1 bg-border" />
      </div>

      <Button
        type="button"
        variant="outline"
        onClick={() => inputRef.current?.click()}
        className="text-primary hover:text-primary"
      >
        <Upload />
        Busca en archivos
      </Button>
    </div>
  )
}
