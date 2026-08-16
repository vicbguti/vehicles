import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { Vehicle } from "@/lib/types"

interface DistributionTableProps {
  vehicles: Vehicle[]
}

export function DistributionTable({ vehicles }: DistributionTableProps) {
  return (
    <Table>
      <TableHeader>
        <TableRow className="hover:bg-transparent">
          <TableHead className="pl-4 text-xs font-medium text-muted-foreground">
            Identificador
          </TableHead>
          <TableHead className="text-xs font-medium text-muted-foreground">Clase</TableHead>
          <TableHead className="text-xs font-medium text-muted-foreground">
            Unidades de Almacenamiento
          </TableHead>
          <TableHead className="pl-4 pr-4 text-xs font-medium text-muted-foreground">
            Cantón
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {vehicles.map((vehicle, index) => (
          <TableRow
            key={vehicle.id}
            className={`border-b-0 ${index % 2 === 1 ? "bg-muted/20 hover:bg-muted/40" : "hover:bg-muted/40"}`}
          >
            <TableCell className="py-2.5 pl-4">{vehicle.id}</TableCell>
            <TableCell className="py-2.5">{vehicle.clase}</TableCell>
            <TableCell className="py-2.5">{vehicle.storage}</TableCell>
            <TableCell className="py-2.5 pl-4 pr-4">{vehicle.canton}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}
