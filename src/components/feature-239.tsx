"use client"

import React from "react"
import { ArrowUpRight, ChevronUp } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

/**
 * Hero Section – Feature 239
 * ----------------------------------------------------------
 * Splash page costruita con Tailwind + shadcn/ui + lucide-react.
 * Importa <Feature239 /> dove vuoi mostrare il blocco.
 */
export function Feature239() {
  return (
    <section className="bg-background py-32">
      <div className="relative container flex flex-col items-center">
        <DottedDiv>
          <div className="grid lg:grid-cols-2">
            {/* Left column -------------------------------------------------- */}
            <div className="flex w-full flex-col gap-8 px-10 py-20 md:px-14">
              <h1 className="text-5xl font-semibold tracking-tighter md:text-7xl">
                La toolbox
                <br />
                definitiva
              </h1>

              <p className="tracking-tight text-muted-foreground md:text-xl">
                Progetto in costruzione
              </p>

              <div className="flex w-full gap-2">
                <Button className="text-md h-12 w-fit rounded-full bg-primary px-10 text-primary-foreground">
                  Get Started
                </Button>
                <Button
                  variant="outline"
                  className="text-md h-12 w-12 rounded-full transition-all ease-in-out hover:rotate-45"
                >
                  <ArrowUpRight />
                </Button>
              </div>
            </div>

            {/* Right column ------------------------------------------------- */}
            <DottedDiv className="group size-full place-self-end p-4 lg:w-4/6">
              <div className="relative h-full w-full bg-muted-2/50 p-4 transition-all ease-in-out group-hover:bg-muted-2">
                {/* Background image */}
                <div className="relative h-full w-full overflow-hidden rounded-3xl">
                  <img
                    src="https://shadcnblocks.com/images/block/photos/simone-hutsch-5oYbG-sEImY-unsplash.jpg"
                    alt="architecture"
                    className="h-full w-full object-cover"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent" />
                </div>

                {/* Overlay content */}
                <div className="absolute top-4 -ml-4 flex h-full w-full flex-col items-center justify-between p-10">
                  <p className="flex w-full items-center text-xl tracking-tighter text-background">
                    2025 <span className="mx-2 h-2.5 w-[1px] bg-white" />
                    March
                  </p>

                  <div className="flex flex-col items-center justify-center">
                    <h2 className="text-center text-6xl font-semibold tracking-tight text-background">
                      New <br />
                      Collection
                    </h2>
                    <div className="mt-2 h-1 w-6 rounded-full bg-background" />
                    <p className="mt-10 max-w-sm px-2 text-center text-lg font-light leading-5 tracking-tighter text-background/80">
                      Discover our latest release of beautifully crafted components.
                    </p>
                  </div>

                  <a
                    href="#"
                    className="group mb-6 flex cursor-pointer flex-col items-center justify-center text-background"
                  >
                    <ChevronUp
                      size={30}
                      className="transition-all ease-in-out group-hover:-translate-y-2"
                    />
                    <p className="text-xl tracking-tight text-background">
                      See All
                    </p>
                  </a>
                </div>
              </div>
            </DottedDiv>
          </div>
        </DottedDiv>
      </div>
    </section>
  )
}

/* ------------------------------------------------------------------------- */
/* Helper – cornice punteggiata attorno ai contenuti                         */
/* ------------------------------------------------------------------------- */
type DottedDivProps = {
  children: React.ReactNode
  className?: string
}

const DottedDiv = ({ children, className }: DottedDivProps) => (
  <div className={cn("relative", className)}>
    {/* bordi orizzontali */}
    <div className="absolute inset-x-4 top-4 h-px bg-muted" />
    <div className="absolute inset-x-4 bottom-4 h-px bg-muted" />

    {/* bordi verticali */}
    <div className="absolute top-4 bottom-4 left-4 w-px bg-muted" />
    <div className="absolute top-4 bottom-4 right-4 w-px bg-muted" />

    {/* puntini agli angoli */}
    <div className="absolute top-[12.5px] left-[12.5px] z-10 size-2 rounded-full bg-foreground" />
    <div className="absolute top-[12.5px] right-[12.5px] z-10 size-2 rounded-full bg-foreground" />
    <div className="absolute bottom-[12.5px] left-[12.5px] z-10 size-2 rounded-full bg-foreground" />
    <div className="absolute right-[12.5px] bottom-[12.5px] z-10 size-2 rounded-full bg-foreground" />

    {children}
  </div>
)
