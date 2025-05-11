# utils_openai.py
import asyncio
import json
import re
import time
from typing import List, Dict, Set
from openai import AsyncOpenAI, OpenAI
from common.prompt import build_messages

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
