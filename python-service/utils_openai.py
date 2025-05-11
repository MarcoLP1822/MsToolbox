# utils_openai.py
import asyncio, json, re, time
from typing import List, Dict, Set
from openai import AsyncOpenAI, OpenAI

_OPENAI_MODEL  = "gpt-4o-mini"
_RETRY_BACKOFF = (1, 2, 4)  # secondi in caso di risposta non valida
_FENCE_RE      = re.compile(r"^```[\w]*\n?|```$", re.S)

def _strip_fences(text: str) -> str:
    return _FENCE_RE.sub("", text).strip()

def _parse_corr(raw: str) -> List[Dict]:
    data = json.loads(raw)
    if "corr" not in data:
        raise ValueError("JSON senza chiave 'corr'")
    return data["corr"]

# ------------------------------------------------------------------ #
#  Costruiamo i messaggi (lo stesso identico schema che usavi prima)
SYSTEM_MSG_BASE = """
Sei un correttore di bozze madrelingua italiano con decenni di esperienza.

• Correggi **solo** refusi, errori ortografici / grammaticali e punteggiatura.  
• Non eliminare, spostare o accorciare parole, frasi o capoversi.  
• Non riformulare lo stile; se una parte è già corretta, lasciala invariata.

NOMI / TERMINI FANTASY ↓  
Se trovi varianti ortografiche dei nomi presenti nell’elenco seguente,
uniforma la grafia a quella esatta dell’elenco.

OUTPUT: restituisci **SOLO JSON** con la chiave `'corr'`
( lista di {id:int, txt:str} ) — niente testo extra.
"""

def build_messages(context: str,
                   payload_json: str,
                   glossary: Set[str]) -> List[Dict]:
    system_msg = SYSTEM_MSG_BASE + "\\nLista: " + ", ".join(sorted(glossary))
    return [
        {"role": "system",    "content": system_msg},
        {"role": "assistant", "content": "Contesto (NON modificare):\\n" + context},
        {"role": "user",      "content": payload_json},
    ]
# ------------------------------------------------------------------ #

async def _chat_async(messages, client):
    for delay in _RETRY_BACKOFF:
        resp = await client.chat.completions.create(
            model=_OPENAI_MODEL,
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=messages,
        )
        try:
            return _parse_corr(_strip_fences(resp.choices[0].message.content))
        except (json.JSONDecodeError, ValueError):
            await asyncio.sleep(delay)
    raise RuntimeError("Risposta non-JSON dopo 3 tentativi")

def _chat_sync(messages, client):
    for delay in _RETRY_BACKOFF:
        resp = client.chat.completions.create(
            model=_OPENAI_MODEL,
            temperature=0.3,
            response_format={"type": "json_object"},
            messages=messages,
        )
        try:
            return _parse_corr(_strip_fences(resp.choices[0].message.content))
        except (json.JSONDecodeError, ValueError):
            time.sleep(delay)
    raise RuntimeError("Risposta non-JSON dopo 3 tentativi")

# ========== FUNZIONI PUBBLICHE (quelle che userai da main.py) ====== #
async def get_corrections_async(payload_json: str,
                                client: AsyncOpenAI,
                                glossary: Set[str],
                                context: str = "") -> List[Dict]:
    msgs = build_messages(context, payload_json, glossary)
    return await _chat_async(msgs, client)

def get_corrections_sync(payload_json: str,
                         client: OpenAI,
                         glossary: Set[str],
                         context: str = "") -> List[Dict]:
    msgs = build_messages(context, payload_json, glossary)
    return _chat_sync(msgs, client)
