import os, uuid, tempfile
from pathlib import Path

import aiofiles
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool

from correttore import run_proofread          # tua funzione che restituisce il path dello zip

app = FastAPI()
CHUNK = 1 * 1024 * 1024  # 1 MB


async def save_upload_tmp(upload: UploadFile) -> Path:
    """Salva l'UploadFile in un file temporaneo senza bloccare l'event-loop."""
    async with aiofiles.tempfile.NamedTemporaryFile(
        "wb", delete=False, suffix=".docx"
    ) as tmp:
        while True:
            chunk = await upload.read(CHUNK)
            if not chunk:
                break
            await tmp.write(chunk)
    return Path(tmp.name)


@app.post("/proofread")
async def proofread(background_tasks: BackgroundTasks, docx: UploadFile = File(...)):
    # 1️⃣ salviamo l'upload
    try:
        in_path = await save_upload_tmp(docx)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore salvataggio file: {e}")

    # 2️⃣ elaboriamo nel threadpool (no blocco I/O/CPU)
    try:
        zip_path = await run_proofread(in_path)
    except Exception as e:
        # se qualcosa va storto mentre elabori, pulisci subito il tmp originale
        os.remove(in_path)
        raise HTTPException(status_code=500, detail=f"Errore correzione: {e}")

    # 3️⃣ pianifichiamo la pulizia post-risposta
    background_tasks.add_task(os.remove, in_path)
    background_tasks.add_task(os.remove, zip_path)

    # 4️⃣ inviamo lo zip
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"{Path(docx.filename).stem}_corretto.zip",
        background=background_tasks,
    )
