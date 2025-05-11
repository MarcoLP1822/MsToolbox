# token_utils.py
import re
WORD_RE = re.compile(r"\w+|\W+")

def tokenize(text: str):
    return WORD_RE.findall(text)

def token_starts(tokens):
    pos, starts = 0, []
    for tok in tokens:
        starts.append(pos)
        pos += len(tok)
    return starts