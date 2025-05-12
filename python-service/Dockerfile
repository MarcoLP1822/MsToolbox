########################### 1) BUILDER STAGE ###########################
FROM python:3.11-bookworm AS builder

# Qualità di vita / velocità build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# — apt con layer cache —
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc git \
    && rm -rf /var/lib/apt/lists/*

# — virtual-env isolato, facile da copiare —
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# — requirements prima del codice: layer pip cache-friendly —
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip \
&& pip install --no-cache-dir -r requirements.txt

########################### 2) RUNTIME STAGE ###########################
FROM python:3.11-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# — portiamo solo la venv già pronta, non toolchain di build —
COPY --from=builder /opt/venv /opt/venv

# — utente non-root leggero —
RUN adduser --disabled-password --gecos '' appuser
WORKDIR /app
USER appuser

# — codice applicativo (risorse leggere) —
COPY --chown=appuser:appuser . .

# — porta esposta & avvio Uvicorn —
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]