import { useEffect, useState } from "react"
import { Cpu } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { getHealth } from "@/lib/api"
import { modelLabel } from "@/lib/models"

/**
 * Modelo que responderá en el servidor, consultado a `GET /api/health`.
 *
 * El modelo se fija al arrancar el API con `FLEET_LOADING_MODEL`, así que
 * basta con preguntarlo una vez al montar.
 */
export function ActiveModelBadge() {
  const [model, setModel] = useState<string | null>(null)
  const [unreachable, setUnreachable] = useState(false)

  useEffect(() => {
    let cancelled = false
    getHealth()
      .then((health) => {
        if (!cancelled) setModel(health.model)
      })
      .catch(() => {
        if (!cancelled) setUnreachable(true)
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (unreachable) {
    return (
      <Badge variant="outline" className="gap-1.5 text-muted-foreground">
        <span className="size-1.5 rounded-full bg-destructive" />
        Servidor no disponible
      </Badge>
    )
  }

  if (model === null) {
    return (
      <Badge variant="outline" className="gap-1.5 text-muted-foreground">
        <span className="size-1.5 animate-pulse rounded-full bg-muted-foreground" />
        Consultando modelo...
      </Badge>
    )
  }

  return (
    <Badge variant="outline" className="gap-1.5 text-muted-foreground">
      <Cpu className="text-primary" />
      Modelo: <span className="font-semibold text-foreground">{modelLabel(model)}</span>
    </Badge>
  )
}
