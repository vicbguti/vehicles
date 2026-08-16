import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { Vehicle } from "@/lib/types"
import { VehicleStatusBadge } from "./VehicleStatusBadge"

interface VehicleTableProps {
  vehicles: Vehicle[]
}

export function VehicleTable({ vehicles }: VehicleTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow className="hover:bg-transparent">
          <TableHead className="pl-5 text-xs font-medium text-muted-foreground">
            Identificador
          </TableHead>
          <TableHead className="text-xs font-medium text-muted-foreground">Clase</TableHead>
          <TableHead className="text-xs font-medium text-muted-foreground">
            Unidades de Almacenamiento
          </TableHead>
          <TableHead className="text-xs font-medium text-muted-foreground">Cantón</TableHead>
          <TableHead className="pl-5 pr-5 text-xs font-medium text-muted-foreground">
            Estado
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {vehicles.map((vehicle, index) => (
          <TableRow
            key={vehicle.id}
            className={`border-b-0 ${index % 2 === 1 ? "bg-muted/30 hover:bg-muted/40" : "hover:bg-muted/40"}`}
          >
            <TableCell className="pl-5 py-3 font-medium">{vehicle.id}</TableCell>
            <TableCell className="py-3">{vehicle.clase}</TableCell>
            <TableCell className="py-3">{vehicle.storage}</TableCell>
            <TableCell className="py-3">{vehicle.canton}</TableCell>
            <TableCell className="pl-5 pr-5 py-3">
              <VehicleStatusBadge vehicle={vehicle} />
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
