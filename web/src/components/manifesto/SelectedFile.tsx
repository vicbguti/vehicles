import { FileText, X } from "lucide-react"
import { Button } from "@/components/ui/button"

interface SelectedFileProps {
  file: File
  onRemove: () => void
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`
}

export function SelectedFile({ file, onRemove }: SelectedFileProps) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-border px-3 py-2.5">
      <FileText className="size-5 shrink-0 text-primary" />
      <div className="flex min-w-0 flex-1 items-baseline gap-2">
        <span className="truncate text-sm font-medium text-foreground">{file.name}</span>
        <span className="shrink-0 text-xs text-muted-foreground">{formatSize(file.size)}</span>
      </div>
      <Button
        type="button"
        variant="ghost"
        size="icon-sm"
        onClick={onRemove}
        className="size-7 rounded-full bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground"
        aria-label="Quitar archivo"
      >
        <X />
      </Button>
    </div>
  )
}
