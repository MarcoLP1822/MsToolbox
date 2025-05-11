# reports.py
"""
Genera i due report Markdown:
  • <nome>_diff.md  – diff delle frasi corrette
  • <nome>_glossario.md – elenco nomi / occorrenze
"""

from __future__ import annotations
from pathlib import Path
from datetime import datetime
import collections, re
from typing import List

# ── dipendenze locali da main.py -------------------------------------
from token_utils import tokenize, token_starts           # se li hai separati
# oppure, se non hai ancora estratto token_utils:
# from main import tokenize, token_starts

from dataclasses import dataclass
from difflib import SequenceMatcher

@dataclass
class Modification:
    par_id: int
    original: str
    corrected: str


# ---------- helpers diff --------------------------------------------
_SENT_SPLIT_RE = re.compile(r"(?<=[\.\!\?…])\s+(?=[A-ZÀ-Ý])", re.U)

def _split_sentences(text: str) -> List[str]:
    return _SENT_SPLIT_RE.split(text.strip())

def _token_diff_markdown(a: str, b: str) -> str:
    tok_a = tokenize(a)
    tok_b = tokenize(b)
    sm = SequenceMatcher(a=tok_a, b=tok_b, autojunk=False)
    out: List[str] = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            out.extend(tok_a[i1:i2])
        elif op == "delete":
            out.extend([f"~~{t}~~" for t in tok_a[i1:i2]])
        elif op == "insert":
            out.extend([f"**{t}**" for t in tok_b[j1:j2]])
        elif op == "replace":
            out.extend([f"~~{t}~~" for t in tok_a[i1:i2]])
            out.extend([f"**{t}**" for t in tok_b[j1:j2]])
    return "".join(out)


# ---------- report diff ---------------------------------------------
def write_markdown_report(mods: List[Modification], dst_doc: Path) -> None:
    md_path = dst_doc.with_name(dst_doc.stem + "_diff.md")

    paragraphs_changed = len(mods)
    deleted_tokens = inserted_tokens = 0
    lines: List[str] = []

    # Header
    lines.append(f"# Report correzioni – {dst_doc.name}")
    lines.append(f"_Generato: {datetime.now():%Y-%m-%d %H:%M}_\n")

    # Corpo
    for m in mods:
        orig_sent = _split_sentences(m.original)
        corr_sent = _split_sentences(m.corrected)
        sm_sent   = SequenceMatcher(a=orig_sent, b=corr_sent, autojunk=False)

        for op, i1, i2, j1, j2 in sm_sent.get_opcodes():
            if op == "equal":
                continue

            orig_block = " ".join(orig_sent[i1:i2]).strip()
            corr_block = " ".join(corr_sent[j1:j2]).strip()

            orig_tok = tokenize(orig_block)
            corr_tok = tokenize(corr_block)
            deleted_tokens  += max(0, len(orig_tok) - len(corr_tok))
            inserted_tokens += max(0, len(corr_tok) - len(orig_tok))

            diff_md = _token_diff_markdown(orig_block, corr_block)
            lines.extend(["---", f"### Paragrafo {m.par_id}", diff_md, ""])

    # Statistiche
    stats_block = [
        "## Statistiche",
        f"* Paragrafi corretti: {paragraphs_changed}",
        f"* Token eliminati (approssimativi): {deleted_tokens}",
        f"* Token inseriti (approssimativi): {inserted_tokens}",
        "", "---", "",
    ]
    lines[2:2] = stats_block

    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"📄  Report modifiche salvato: {md_path.name}")


# ---------- report glossario ----------------------------------------
def write_glossary_report(glossary: set[str],
                          all_paras,
                          dst_doc: Path) -> None:
    counts = collections.Counter(
        w for p in all_paras for w in re.findall(r"\b(?:[A-Z][a-z]{2,}|[A-Z]{2,})\w*\b", p.text)
        if w in glossary
    )

    md_path = dst_doc.with_name(dst_doc.stem + "_glossario.md")
    lines = [
        f"# Glossario finale – {dst_doc.name}",
        f"_Generato: {datetime.now():%Y-%m-%d %H:%M}_",
        "",
        "| Nome | Occorrenze |",
        "|------|-----------:|",
    ]
    for w in sorted(glossary, key=str.lower):
        lines.append(f"| {w} | {counts[w]} |")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"📑  Glossario salvato: {md_path.name}")
