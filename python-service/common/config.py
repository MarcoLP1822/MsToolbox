# python-service/common/config.py
"""
Config centralizzato per tutta la python-service.

Modifica qui il modello, il back-off o altri parametri globali:
   • OPENAI_MODEL
   • MAX_TOKENS_MODEL
   • RETRY_BACKOFF
"""

from __future__ import annotations
import os
from dotenv import load_dotenv
load_dotenv()
# ———————————————————————————————————————————
OPENAI_MODEL: str = "gpt-4o-mini"   # modello usato dai client OpenAI

# lunghezza massima di contesto che vogliamo passare al modello
MAX_TOKENS_MODEL: int = 10_000

# ritardi (in secondi) se la risposta non è valida → 1° tentativo, 2°, 3°…
RETRY_BACKOFF: tuple[int, ...] = (1, 2, 4)

# API-key letta dall’ambiente, se ti fa comodo tenerla qui
OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
# ———————————————————————————————————————————
