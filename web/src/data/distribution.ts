import type { DistributionGroup } from "@/lib/types"

export const initialDistribution: DistributionGroup[] = [
  {
    id: "camion-a",
    name: "Camión A",
    capacity: 6,
    vehicles: [
      { id: "2024_4335", clase: "JEEP", storage: "1.8", canton: "21701", status: "accepted" },
      { id: "2024_24370", clase: "AUTO", storage: "1.0", canton: "21701", status: "accepted" },
      { id: "2024_39227", clase: "AUTO", storage: "1.0", canton: "21701", status: "accepted" },
      { id: "2024_45028", clase: "MOTO", storage: "0.6", canton: "21701", status: "accepted" },
      { id: "2024_88528", clase: "AUTO", storage: "1.0", canton: "21701", status: "accepted" },
      { id: "2024_121058", clase: "AUTO", storage: "1.0", canton: "21701", status: "accepted" },
    ],
  },
  {
    id: "camion-b",
    name: "Camión B",
    capacity: 6,
    vehicles: [
      { id: "2024_124219", clase: "JEEP", storage: "1.8", canton: "21701", status: "accepted" },
      { id: "2024_133301", clase: "MOTO", storage: "0.6", canton: "21701", status: "accepted" },
    ],
  },
  {
    id: "sin-camion",
    name: "Sin Camión",
    vehicles: [
      { id: "2024_24289", clase: "JEEP", storage: "-", canton: "21701", status: "rejected" },
      { id: "2024_80592", clase: "MOTO", storage: "0.6", canton: "-", status: "rejected" },
      { id: "2024_117652", clase: "-", storage: "-", canton: "-", status: "rejected" },
      { id: "2024_133302", clase: "JEEP", storage: "6.2", canton: "21701", status: "rejected" },
    ],
  },
]
