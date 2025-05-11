from typing import List, Dict, Set
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