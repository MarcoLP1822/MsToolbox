"use client"

import { useRef, useState } from "react"
import { UploadCloud } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export default function CorrezioneBozzePage() {
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [outUrl, setOutUrl] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  async function handleUpload() {
    if (!file) return
    setBusy(true)
    const form = new FormData()
    form.append("docx", file)
    const res = await fetch("/api/proofread", { method: "POST", body: form })
    const blob = await res.blob()            // zip (docx + md)
    setOutUrl(URL.createObjectURL(blob))
    setBusy(false)
  }

  return (
    <main className="container flex flex-col gap-6 py-10">

      {/* ••• DROP ZONE ••• */}
      <label
        htmlFor="docx"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault()
          const f = e.dataTransfer.files?.[0]
          if (f?.name.endsWith(".docx")) setFile(f)
        }}
        className={cn(
          "mx-auto w-full max-w-3xl",
          "flex flex-col items-center justify-center gap-2 rounded-lg",
          "border-2 border-dashed border-muted-foreground/40 px-6 py-12 text-center",
          "cursor-pointer transition hover:bg-muted/50"
        )}
      >
        <UploadCloud className="h-8 w-8" />
        <p className="text-sm">
          Trascina qui il tuo <strong>.docx</strong> oppure{" "}
          <span className="underline">clicca per selezionarlo</span>
        </p>
        {file && <p className="mt-2 text-sm font-medium">{file.name}</p>}
      </label>

      {/* input nascosto */}
      <input
        ref={inputRef}
        id="docx"
        type="file"
        accept=".docx"
        className="sr-only"
        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
      />

      {/* CTA */}
      <Button
        className="w-full sm:w-fit mx-auto max-w-3xl"
        disabled={!file || busy}
        onClick={handleUpload}
      >
        {busy ? "Attendi…" : "Avvia correzione"}
      </Button>

      {/* Link di download */}
      {outUrl && (
        <a
          href={outUrl}
          download="corretto.zip"
          className="w-fit text-primary underline mx-auto max-w-3xl"
        >
          Scarica risultato
        </a>
      )}
    </main>
  )
}
