import type { Truck, Vehicle } from "@/lib/types"

/** El plan de distribución como CSV punto y coma: el manifiesto (identificador;
 *  clase;cu;canton) más la columna `camion` con el camión asignado
 *  (``CAMION_N`` o ``SIN CAMION``). Es el output del app, en el mismo formato
 *  que el input. */
export function distributionToCsv(trucks: Truck[], sinCamion: Vehicle[]): string {
  const rows = ["identificador;clase;cu;canton;camion"]
  for (const truck of trucks) {
    for (const vehicle of truck.vehicles) {
      rows.push(
        [vehicle.identificador, vehicle.clase, vehicle.cu, vehicle.canton, truck.id].join(";"),
      )
    }
  }
  for (const vehicle of sinCamion) {
    rows.push([vehicle.identificador, vehicle.clase, vehicle.cu, vehicle.canton, "SIN CAMION"].join(";"))
  }
  return rows.join("\n") + "\n"
}

export function downloadText(filename: string, content: string) {
  const blob = new Blob([content], { type: "text/csv;charset=utf-8" })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement("a")
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}