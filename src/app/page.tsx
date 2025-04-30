"use client"

import { AppSidebar } from "@/components/app-sidebar"
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar"
import { SiteHeader } from "@/components/site-header"
import { Feature239 } from "@/components/feature-239"

/**
 * Home page
 * Mostra l'hero <Feature239 /> e, se vuoi,
 * mantiene header e sidebar in stile dashboard.
 */
export default function Page() {
  return (
    <SidebarProvider>
      {/* Sidebar sinistra -------------------------------------------------- */}
      <AppSidebar variant="inset" />

      {/* Contenuto principale -------------------------------------------- */}
      <SidebarInset>
        {/* Header in alto */}
        <SiteHeader />

        {/* Hero / splash section */}
        <Feature239 />
      </SidebarInset>
    </SidebarProvider>
  )
}
