"use client"

import { usePathname } from "next/navigation"
import { FolderIcon } from "lucide-react"

// mappa slug → titolo
const TITLE_BY_ROUTE: Record<string, string> = {
  "": "Dashboard",            //  /
  "correzione-bozze": "Correzione bozze",
  analytics: "Analytics",
  projects: "Projects",
  team: "Team",
}

export function SiteHeader() {
  const pathname = usePathname()                   // es. "/correzione-bozze"
  const segments = pathname.split("/").filter(Boolean) // ["correzione-bozze"]
  const slug = segments.at(-1) ?? ""               // ultimo segmento o ""

  const title = TITLE_BY_ROUTE[slug] ?? "Marco's Toolbox"

  return (
    <header className="flex items-center gap-3 border-b px-6 py-4">
      <FolderIcon className="size-5 shrink-0" />
      <h1 className="text-lg font-semibold tracking-tight">{title}</h1>
    </header>
  )
}
