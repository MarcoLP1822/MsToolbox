# --- Base image --------------------------------------------------------
    FROM python:3.11-slim AS runtime

    # 1. ottimizzazioni pip / runtime (root)
    ENV PYTHONUNBUFFERED=1 \
        PIP_NO_CACHE_DIR=1
    
    WORKDIR /app
    
    # 2. dipendenze  --------------------------------------------------------
    COPY requirements.txt .
    RUN pip install -r requirements.txt         # installa come root → /usr/local
    
    # 3. crea utente non-root e passa i permessi ---------------------------
    RUN adduser --disabled-password --gecos '' appuser
    USER appuser
    
    # 4. copia sorgente (con ownership corretta) ---------------------------
    COPY --chown=appuser:appuser . .
    
    # 5. entrypoint ---------------------------------------------------------
    CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
    