# correttore.py
"""
Corregge grammatica e ortografia in **qualsiasi** parte di un documento
Word (.docx) e produce un report Markdown con tutte le modifiche.

* testo normale, anche in tabelle nidificate
* header & footer
* testo delle note a piè di pagina (footnotes)
* caselle di testo / forme (<w:txbxContent>)

Mantiene corsivi, grassetti, sottolineature, riferimenti di nota, ecc.
Richiede **python-docx ≥ 0.8.11**.
"""

from __future__ import annotations
import os
import re
import time
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from openai import OpenAI

# ───────────────────────── CONFIGURAZIONE ────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY non trovata nelle variabili d’ambiente "
        "(esporta la chiave o aggiungila nel file .env)"
    )

OPENAI_MODEL = "gpt-4o-mini"
MAX_TOKENS_GPT4O_MINI = 8_000

# ─────────────────────────────────────────────────────────────────────

WORD_RE = re.compile(r"\w+|\W+")

# ╭─────────────────────────── Note a piè di pagina ▾──────────────────────────╮
import os, shutil, zipfile, tempfile
from pathlib import Path
from collections import defaultdict
from copy import deepcopy
from lxml import etree
from docx.oxml.ns import qn  # già presente nel file principale

def correggi_footnotes_xml(docx_path: Path, client) -> None:
    """
    Corregge il testo delle note a piè di pagina in word/footnotes.xml
    distribuendo le parole corrette nei <w:t> originali (token-level) e
    ripristinando il grassetto/italico del primo run se viene perso.
    """
    # cartella di lavoro sicura e sempre scrivibile
    tmp_dir = tempfile.mkdtemp(prefix="footnotes_", dir="/tmp")

    # ── 1. Estrai il .docx ─────────────────────────────────────────────
    with zipfile.ZipFile(docx_path, "r") as zf:
        zf.extractall(tmp_dir)

    footnotes_file = os.path.join(tmp_dir, "word", "footnotes.xml")
    if not os.path.exists(footnotes_file):
        shutil.rmtree(tmp_dir)
        return                                          # nessuna nota

    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    tree = etree.parse(footnotes_file)

    # ── 2. Scorri ogni nota (escludi i separator) ──────────────────────
    for foot in tree.xpath("//w:footnote[not(@w:type='separator')]", namespaces=ns):
        txt_nodes = foot.xpath(".//w:t", namespaces=ns)
        full_text = "".join(n.text or "" for n in txt_nodes)

        if not full_text.strip():
            continue

        # 2a. Chiamata GPT identica a quella dei paragrafi
        messages = [
            {
                "role": "system",
                "content": (
                    "Sei un correttore di bozze italiano madrelingua "
                    "dall'esperienza pluridecennale. Correggi solo errori "
                    "ortografici e grammaticali. Restituisci solo il testo "
                    "corretto, senza commenti."
                ),
            },
            {"role": "user", "content": full_text},
        ]
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.7,
            messages=messages,
        )
        corrected = resp.choices[0].message.content.strip()
        if corrected == full_text:
            continue                                  # nessuna correzione

        # ── 2b. Redistribuisci le parole corrette token-level ─────────
        orig_tok = tokenize(full_text)
        corr_tok = tokenize(corrected)
        mapping  = align_tokens(orig_tok, corr_tok)

        starts_orig = token_starts(orig_tok)

        # mappa “carattere originale → indice nodo <w:t>”
        char2node = []
        for idx, n in enumerate(txt_nodes):
            char2node.extend([idx] * len(n.text or ""))

        tok_per_node = defaultdict(list)

        for ref_idx, tok in mapping:
            # se il token non deriva da nulla (insert/delete) scegli nodo vicino
            if ref_idx is None or ref_idx >= len(starts_orig):
                node_idx = 0
            else:
                char_pos = starts_orig[ref_idx]
                node_idx = char2node[min(char_pos, len(char2node) - 1)]
            tok_per_node[node_idx].append(tok)

        # scrivi il testo nei nodi senza spezzare parole
        for idx, n in enumerate(txt_nodes):
            n.text = "".join(tok_per_node.get(idx, []))

        # ── 2c. Ripristina il grassetto/italico del primo run se perso ─
        first_with_txt = None
        for n in txt_nodes:
            if n.text and n.text.strip():
                first_with_txt = n
                break

        if first_with_txt is not None:
            run_first = first_with_txt.getparent()
            has_rPr_first = run_first.find("./w:rPr", namespaces=ns)
            has_bold_first = run_first.xpath("./w:rPr/w:b", namespaces=ns)

            if not has_bold_first:
                # cerca un altro run con formattazione
                for n2 in txt_nodes:
                    if n2 is first_with_txt or not (n2.text and n2.text.strip()):
                        continue
                    rPr_other = n2.getparent().find("./w:rPr", namespaces=ns)
                    if rPr_other is not None and list(rPr_other):
                        # se il primo non ha <w:rPr>, crealo
                        if has_rPr_first is None:
                            has_rPr_first = etree.SubElement(run_first, qn("w:rPr"))
                        # copia profonda di TUTTO il rPr (grassetto, italico, ecc.)
                        for child in rPr_other:
                            has_rPr_first.append(deepcopy(child))
                        break  # basta una volta

    # ── 3. Salva e ricompatta il .docx ─────────────────────────────────
    tree.write(footnotes_file, xml_declaration=True, encoding="utf-8")

    tmp_docx = docx_path.with_suffix(".tmp")
    with zipfile.ZipFile(tmp_docx, "w") as zf:
        for root, _, files in os.walk(tmp_dir):
            for f in files:
                fullpath = os.path.join(root, f)
                arcname = os.path.relpath(fullpath, tmp_dir)
                zf.write(fullpath, arcname)

    shutil.move(tmp_docx, docx_path)
    shutil.rmtree(tmp_dir)
    print("✏️  Note a piè di pagina corrette e formattazione preservata")

# ╭─────────────────────────── Utility token ▾──────────────────────────╮
def tokenize(text: str) -> List[str]:
    """Tokenizzazione grezza (regex) — sufficiente per stimare la
    lunghezza in token senza dipendenze esterne."""
    return WORD_RE.findall(text)


def token_starts(tokens: List[str]) -> List[int]:
    pos = 0
    starts = []
    for tok in tokens:
        starts.append(pos)
        pos += len(tok)
    return starts
# ╰──────────────────────────────────────────────────────────────────────╯

# ╭─────────────────────────── Data-model modifiche ▾────────────────────╮
@dataclass
class Modification:
    par_id: int
    original: str
    corrected: str
# ╰──────────────────────────────────────────────────────────────────────╯

# ╭─────────────────────────── Chunking ▾────────────────────────────────╮
def chunk_paragraph_objects(
    paragraphs: List[Paragraph],
    max_tokens: int = MAX_TOKENS_GPT4O_MINI,
) -> List[List[Paragraph]]:
    """Dividi la lista di oggetti Paragraph in blocchi < max_tokens."""
    chunks: List[List[Paragraph]] = []
    current: List[Paragraph] = []
    current_tokens = 0

    for p in paragraphs:
        para_tokens = len(tokenize(p.text))

        if current and current_tokens + para_tokens > max_tokens:
            chunks.append(current)
            current = [p]
            current_tokens = para_tokens
        else:
            current.append(p)
            current_tokens += para_tokens

        # paragrafo singolo > soglia
        if not current and para_tokens > max_tokens:
            chunks.append([p])
            current_tokens = 0

    if current:
        chunks.append(current)
    return chunks
# ╰──────────────────────────────────────────────────────────────────────╯

# ╭─────────────────────────── Diff token-level ▾────────────────────────╮
def align_tokens(orig: List[str], corr: List[str]) -> List[Tuple[Optional[int], str]]:
    sm = SequenceMatcher(a=orig, b=corr, autojunk=False)
    out: List[Tuple[Optional[int], str]] = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            for k in range(i2 - i1):
                out.append((i1 + k, corr[j1 + k]))
        elif op == "replace":
            inherit = i1 if i1 < len(orig) else None
            for k in range(j2 - j1):
                out.append((inherit, corr[j1 + k]))
        elif op == "insert":
            inherit = i1 - 1 if i1 > 0 else None
            for k in range(j1, j2):
                out.append((inherit, corr[k]))
    return out
# ╰──────────────────────────────────────────────────────────────────────╯

# ╭─────────────────────────── Helpers copy RUN ▾────────────────────────╮
def copy_rPr(src_rPr, dest_run):
    if src_rPr is None:
        return
    dest = dest_run._r.get_or_add_rPr()
    dest.clear()
    for child in src_rPr:
        dest.append(deepcopy(child))


def clone_run(src_run, paragraph):
    new_run = paragraph.add_run("")
    copy_rPr(src_run._r.rPr, new_run)
    for child in src_run._r:
        if child.tag != qn("w:t"):
            new_run._r.append(deepcopy(child))
    return new_run
# ╰──────────────────────────────────────────────────────────────────────╯

# ╭─────────────────────────── Map char→run ▾────────────────────────────╮
def char_to_run_map(paragraph) -> List[int]:
    mapping: List[int] = []
    for idx, run in enumerate(paragraph.runs):
        mapping.extend([idx] * len(run.text))
    return mapping
# ╰──────────────────────────────────────────────────────────────────────╯

# ╭─────────────────────────── Correzione singolo paragrafo ▾────────────╮
def correct_paragraph(
    p: Paragraph,
    client: OpenAI,
    mods: List[Modification],
    par_id: int,
    prev_text: Optional[str] = None,
):
    original = p.text
    if not original.strip():
        return  # ignora paragrafi vuoti

    # costruisci messaggi con contesto
    messages = [
        {
            "role": "system",
            "content": (
                "Sei un correttore di bozze italiano madrelingua professionista "
                "dall'esperienza pluridecennale. Correggi solo errori ortografici "
                "e grammaticali che trovi nel testo. Restituisci solo il testo "
                "corretto. Evita prosa superflua e commenti. Evita la correzione "
                "di nomi di persona non italiani o nomi fantasy."
            ),
        }
    ]
    if prev_text:
        messages.append({
            "role": "user",
            "content": f"Paragrafo precedente (per contesto):\n{prev_text}"
        })
    messages.append({"role": "user", "content": original})

    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.7,
        messages=messages,
    )
    corrected = resp.choices[0].message.content.strip()
    if corrected == original:
        return

    # Salva la modifica per il report
    mods.append(Modification(par_id=par_id, original=original, corrected=corrected))

    # Ricostruzione runs mantenendo formattazione
    orig_tokens = tokenize(original)
    corr_tokens = tokenize(corrected)
    mapping_tok = align_tokens(orig_tokens, corr_tokens)

    starts_orig = token_starts(orig_tokens)
    char_run = char_to_run_map(p)

    tokens_per_run: Dict[int, List[str]] = defaultdict(list)
    for ref_idx, tok in mapping_tok:
        if ref_idx is None or ref_idx >= len(starts_orig):
            run_idx = char_run[0] if char_run else 0
        else:
            char_pos = starts_orig[ref_idx]
            run_idx = char_run[char_pos]
        tokens_per_run[run_idx].append(tok)

    old_runs = list(p.runs)
    p._p.clear_content()

    for idx, run in enumerate(old_runs):
        toks = tokens_per_run.get(idx, [])
        if run.text:
            if not toks:
                continue  # rimuove run residui
            new_run = clone_run(run, p)
            new_run.text = "".join(toks)
        else:
            p._p.append(deepcopy(run._r))  # footnote, commenti, ecc.
# ╰──────────────────────────────────────────────────────────────────────╯

# ───────────────────────── traversal del documento ─────────────────────────────
def iter_body_paragraphs(container) -> Iterable[Paragraph]:
    for para in container.paragraphs:
        yield para
    for tbl in getattr(container, "tables", []):
        for row in tbl.rows:
            for cell in row.cells:
                yield from iter_body_paragraphs(cell)


def iter_footnote_paragraphs(doc: Document) -> Iterable[Paragraph]:
    fpart = getattr(doc.part, "footnotes_part", None)
    if fpart:
        for footnote in fpart.footnotes:
            for para in footnote.paragraphs:
                yield para


def iter_header_footer_paragraphs(doc: Document) -> Iterable[Paragraph]:
    for sect in doc.sections:
        for hf in (sect.header, sect.footer):
            if hf:
                yield from iter_body_paragraphs(hf)


def iter_textbox_paragraphs(doc: Document) -> Iterable[Paragraph]:
    parts = [doc.part]
    for sect in doc.sections:
        parts.extend([sect.header.part, sect.footer.part])
    fpart = getattr(doc.part, "footnotes_part", None)
    if fpart:
        parts.append(fpart)
    for part in parts:
        root = part._element
        for txbx in root.xpath('.//*[local-name()="txbxContent"]'):
            for p_el in txbx.xpath('.//*[local-name()="p"]'):
                yield Paragraph(p_el, part)


def iter_all_paragraphs(doc: Document) -> Iterable[Paragraph]:
    yield from iter_body_paragraphs(doc)
    yield from iter_footnote_paragraphs(doc)
    yield from iter_header_footer_paragraphs(doc)
    yield from iter_textbox_paragraphs(doc)
# ────────────────────────────────────────────────────────────────────────────────

# ╭─────────────────────────── Markdown report ▾─────────────────────────╮
import re
from difflib import SequenceMatcher

# regex molto basilare per spezzare in frasi (., ?, !, … seguiti da spazio + maiuscola)
_SENT_SPLIT_RE = re.compile(r"(?<=[\.\!\?…])\s+(?=[A-ZÀ-Ý])", re.U)

def _split_sentences(text: str) -> List[str]:
    """Suddivide un paragrafo in frasi usando una regex semplificata."""
    return _SENT_SPLIT_RE.split(text.strip())

def _token_diff_markdown(a: str, b: str) -> str:
    """Restituisce un diff token-level in Markdown (~~del~~ / **ins**)."""
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

def write_markdown_report(mods: List[Modification], dst_doc: Path):
    """Crea un report Markdown limitato **solo alle frasi modificate**."""
    md_path = dst_doc.with_name(dst_doc.stem + "_diff.md")

    paragraphs_changed = len(mods)
    deleted_tokens = 0
    inserted_tokens = 0
    lines: List[str] = []

    # Header
    lines.append(f"# Report correzioni – {dst_doc.name}")
    lines.append(f"_Generato: {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n")

    # Corpo
    for m in mods:
        orig_sent = _split_sentences(m.original)
        corr_sent = _split_sentences(m.corrected)

        sm_sent = SequenceMatcher(a=orig_sent, b=corr_sent, autojunk=False)

        for op, i1, i2, j1, j2 in sm_sent.get_opcodes():
            if op == "equal":
                continue  # frasi identiche → salta

            orig_block = " ".join(orig_sent[i1:i2]).strip()
            corr_block = " ".join(corr_sent[j1:j2]).strip()

            orig_tok = tokenize(orig_block)
            corr_tok = tokenize(corr_block)
            deleted_tokens += max(0, len(orig_tok) - len(corr_tok))
            inserted_tokens += max(0, len(corr_tok) - len(orig_tok))

            diff_md = _token_diff_markdown(orig_block, corr_block)

            lines.extend([
                "---",
                f"### Paragrafo {m.par_id}",
                diff_md,
                "",
            ])

    # Statistiche
    stats_block = [
        "## Statistiche",
        f"* Paragrafi corretti: {paragraphs_changed}",
        f"* Token eliminati (approssimativi): {deleted_tokens}",
        f"* Token inseriti (approssimativi): {inserted_tokens}",
        "",
        "---",
        "",
    ]
    lines[2:2] = stats_block  # inserisce subito dopo header

    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"📄  Report modifiche salvato: {md_path.name}")
# ╰──────────────────────────────────────────────────────────────────────╯

# ───────────────────────── entry-point con logging dei chunk ───────────────────
def process_doc(inp: Path, out: Path):
    client = OpenAI(api_key=OPENAI_API_KEY)
    doc = Document(inp)

    all_paras: List[Paragraph] = list(iter_all_paragraphs(doc))
    para_chunks = chunk_paragraph_objects(all_paras)

    mods: List[Modification] = []
    par_counter = 0

    total_chunks = len(para_chunks)
    print(
        f"🔍  Rilevati {total_chunks} chunk "
        f"(limite {MAX_TOKENS_GPT4O_MINI} token)."
    )

    for chunk_idx, chunk in enumerate(para_chunks, 1):
        print(
            f"⚙️  Elaborazione chunk {chunk_idx}/{total_chunks} "
            f"({len(chunk)} paragrafi)…"
        )
        prev = None
        for p in chunk:
            par_counter += 1
            correct_paragraph(p, client, mods, par_counter, prev)
            prev = p.text
        print(f"✅  Completato chunk {chunk_idx}/{total_chunks}")

    doc.save(out)
    print(f"💾  Documento salvato: {out.name}")

    correggi_footnotes_xml(out, client)


    # Genera report Markdown
    write_markdown_report(mods, out)

def find_latest_docx(folder: Path) -> Path:
    files = list(folder.glob("*.docx"))
    if not files:
        raise RuntimeError("Nessun .docx trovato nella cartella")
    return max(files, key=lambda p: p.stat().st_mtime)

if __name__ == "__main__":
    # marca inizio
    start_time = time.perf_counter()

    here = Path(__file__).resolve().parent
    src = find_latest_docx(here)
    dst = src.with_stem(src.stem + "_corretto")
    print(f"📝  Correggo {src.name} → {dst.name} …")
    process_doc(src, dst)

    # tempo impiegato
    elapsed = time.perf_counter() - start_time
    print(f"✨  Fatto in {elapsed:.2f} secondi!")

def run_proofread(src_path: Path) -> Path:
    """
    Wrapper usato dall'API: prende un .docx,
    restituisce Path del .zip con docx corretto + md.
    """
    dst = src_path.with_stem(src_path.stem + "_corretto")
    process_doc(src_path, dst)

    # impacchetta risultato + report
    zip_path = dst.with_suffix(".zip")
    import zipfile
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(dst, dst.name)
        zf.write(dst.with_name(dst.stem + "_diff.md"),
                 dst.stem + "_diff.md")

    return zip_path
