from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from tempfile import NamedTemporaryFile
from correttore import run_proofread
from pathlib import Path

app = FastAPI()

@app.post("/proofread")
async def proofread(docx: UploadFile = File(...)):
    if not docx.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="Serve un .docx")

    with NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        data = await docx.read()
        tmp.write(data)
        tmp_path = tmp.name

    zip_path = run_proofread(Path(tmp_path))
    return FileResponse(zip_path, filename="corretto.zip")
