// src/app/api/proofread/route.ts
import { NextRequest } from "next/server";

export const runtime = "nodejs";          // 👉 forza l’esecuzione su Node

export async function POST(req: NextRequest) {
  const pyRes = await fetch(
    `${process.env.PY_SERVICE_URL}/proofread`,
    {
      method: "POST",
      headers: {
        // inoltra lo stesso boundary del multipart
        "Content-Type": req.headers.get("content-type") ?? "",
      },
      body: req.body,                    // stream originale
      duplex: "half",                    // 👈 obbligatorio con body streaming
    },
  );

  if (!pyRes.ok) {
    return new Response(await pyRes.text(), { status: pyRes.status });
  }

  return new Response(pyRes.body, {
    status: 200,
    headers: {
      "Content-Type": "application/zip",
      "Content-Disposition": 'attachment; filename="corretto.zip"',
    },
  });
}
