"use client"

import { useRef, useState, useEffect } from "react"
import { UploadCloud } from "lucide-react"
import JSZip from "jszip"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

/* ───────── helpers ───────── */
function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onloadend = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })
}

function base64ToBlob(b64: string): Blob {
  const [meta, data] = b64.split(",", 2)
  const mime =
    /data:(.*?);base64/.exec(meta)?.[1] ?? "application/octet-stream"
  const bytes = Uint8Array.from(atob(data), (c) => c.charCodeAt(0))
  return new Blob([bytes], { type: mime })
}

/* ───────── component ───────── */
export default function CorrezioneBozzePage() {
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [url, setUrl] = useState<string | null>(null) // objectURL ZIP
  const [report, setReport] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  /* ---- restore from localStorage al mount ---- */
  useEffect(() => {
    const md = localStorage.getItem("proofreadReport")
    const b64 = localStorage.getItem("proofreadZipB64")

    if (md) setReport(md)

    if (b64) {
      const restoredBlob = base64ToBlob(b64)
      const restoredUrl = URL.createObjectURL(restoredBlob)
      setUrl(restoredUrl)
    }

    return () => {
      if (url) {
        URL.revokeObjectURL(url)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  /* ---- upload handler ---- */
  async function handleUpload() {
    if (!file) return
    setBusy(true)
    setError(null)

    try {
      const form = new FormData()
      form.append("docx", file)
      const res = await fetch("/api/proofread", { method: "POST", body: form })

      if (!res.ok) throw new Error(`Errore ${res.status}`)

      const blob = await res.blob()
      const objectUrl = URL.createObjectURL(blob)
      setUrl(objectUrl)

      /* estrai report .md dallo zip */
      try {
        const zip = await JSZip.loadAsync(blob)
        const mdFile = zip.file(/\.md$/i)?.[0]
        if (mdFile) {
          const mdText = await mdFile.async("string")
          setReport(mdText)
          localStorage.setItem("proofreadReport", mdText)
        }
      } catch (zipErr) {
        console.warn("Impossibile estrarre il report .md", zipErr)
      }

      /* salva lo zip (solo se <5 MB) */
      if (blob.size < 5 * 1024 * 1024) {
        try {
          const b64 = await blobToBase64(blob)
          localStorage.setItem("proofreadZipB64", b64)
        } catch (b64Err) {
          console.warn("Impossibile salvare lo ZIP", b64Err)
        }
      } else {
        localStorage.removeItem("proofreadZipB64")
      }

      /* download automatico */
      const link = document.createElement("a")
      link.href = objectUrl
      link.download = "corretto.zip"
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      /* reset drop-zone */
      setFile(null)
      if (inputRef.current) {
        inputRef.current.value = ""
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Errore sconosciuto"
      setError(`Impossibile completare la correzione: ${msg}`)
    } finally {
      setBusy(false)
    }
  }

  /* ---- UI ---- */
  return (
    <main className="container flex flex-col gap-6 py-10">
      {/* DROP ZONE */}
      <label
        htmlFor="docx"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault()
          const dropped = e.dataTransfer.files?.[0]
          if (dropped?.name.endsWith(".docx")) setFile(dropped)
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
        {file ? (
          <p className="mt-2 text-sm font-medium">{file.name}</p>
        ) : null}
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
        className="mx-auto w-full max-w-3xl sm:w-fit"
        disabled={!file || busy}
        onClick={handleUpload}
      >
        {busy ? "Attendi…" : "Avvia correzione"}
      </Button>

      {/* link manuale + errori */}
      {url ? (
        <a
          href={url}
          download="corretto.zip"
          className="mx-auto w-fit max-w-3xl text-primary underline"
        >
          Scarica risultato di nuovo
        </a>
      ) : null}

      {error ? (
        <p className="mx-auto max-w-3xl text-center text-destructive">
          {error}
        </p>
      ) : null}

      {/* VIEWER */}
      {report ? (
        <section className="prose dark:prose-invert mx-auto w-full max-w-3xl rounded-md border p-6">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{report}</ReactMarkdown>
        </section>
      ) : null}
    </main>
  )
}
