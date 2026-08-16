import { BrowserRouter, Route, Routes } from "react-router-dom"
import { ManifestoPage } from "@/components/manifesto/ManifestoPage"
import { DistributionPage } from "@/components/distribution/DistributionPage"

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ManifestoPage />} />
        <Route path="/distribution" element={<DistributionPage />} />
      </Routes>
    </BrowserRouter>
  )
}
