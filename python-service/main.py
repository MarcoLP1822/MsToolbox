# ----- imports -----
import os
from pathlib import Path
import aiofiles
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from correttore import run_proofread    # è ASYNC!

app = FastAPI()
CHUNK = 1 * 1024 * 1024  # 1 MB

async def save_upload_tmp(upload: UploadFile) -> Path:
    async with aiofiles.tempfile.NamedTemporaryFile("wb", delete=False, suffix=".docx") as tmp:
        while (chunk := await upload.read(CHUNK)):
            await tmp.write(chunk)
    return Path(tmp.name)

@app.post("/proofread")
async def proofread(background_tasks: BackgroundTasks,
                    docx: UploadFile = File(...)):
    try:
        in_path = await save_upload_tmp(docx)
    except Exception as e:
        raise HTTPException(500, f"Errore salvataggio file: {e}")

    try:
        zip_path = await run_proofread(in_path)      # ⬅️  await diretto
    except Exception as e:
        os.remove(in_path)
        raise HTTPException(500, f"Errore correzione: {e}")

    background_tasks.add_task(os.remove, in_path)
    background_tasks.add_task(os.remove, zip_path)

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"{Path(docx.filename).stem}_corretto.zip",
        background=background_tasks,
    )
