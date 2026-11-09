# Inputs for text-search/python/extract-msmarco.py::extract_documents, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import importlib
import random

# --- import the module (file name is not an identifier) ------------------
_mod = importlib.import_module('extract-msmarco')
extract_documents = _mod.extract_documents

# --- point the module's globals at files under WORKDIR -------------------
_mod.download_dir = str(WORKDIR)
_mod.docs_file = str(WORKDIR / "docs.tsv")
_mod.offset_file = str(WORKDIR / "docs-offset.tsv")

_DOC_FILE = WORKDIR / "msmarco-docs.tsv"

# --- data generation -----------------------------------------------------
_VOCAB = (
    "corrosion resistance install with care the quick brown fox jumps over lazy dog "
    "data search engine document ranking query relevance passage retrieval neural "
    "network model system user interface design pattern algorithm complexity "
    "machine learning python code test benchmark performance memory cache index"
).split()

_UNI_WORDS = [
    "café", "naïve", "résumé", "日本語", "テスト", "über", "señor", "Zürich",
    "Москва", "Ελλάδα", "中文", "مرحبا", "Привет", "mañana", "año", "città",
]

_PUNCT = [".", ",", ";", ":", "!", "?", "(", ")", "[", "]", "{", "}",
          "-", "/", "\\", "'", '"', "*", "+", "=", "<", ">", "@", "#"]


def _camel_run(rng, nwords):
    s = _VOCAB[rng.randrange(len(_VOCAB))]
    for _ in range(nwords - 1):
        w = _VOCAB[rng.randrange(len(_VOCAB))]
        s += w[0].upper() + w[1:]
    return s


def _sentence(rng, n):
    return " ".join(_VOCAB[rng.randrange(len(_VOCAB))] for _ in range(n))


def _uni_sentence(rng, n):
    return " ".join(_UNI_WORDS[rng.randrange(len(_UNI_WORDS))] for _ in range(n))


def _punct_sentence(rng, n):
    out = []
    for _ in range(n):
        out.append(_VOCAB[rng.randrange(len(_VOCAB))])
        if rng.random() < 0.6:
            out.append(_PUNCT[rng.randrange(len(_PUNCT))])
    return " ".join(out)


def _build_pool(n=6000):
    rng = random.Random(0)
    docids = []
    offsets = []
    lines = []
    pos = 0
    for i in range(n):
        docid = "D{0:07d}".format(i)
        url = "http://example{0}.com/doc/{1}".format(i % 97, i)
        if i < 1500:
            # camelCase heavy (exercises the look-behind split)
            title = " ".join(_camel_run(rng, rng.randint(2, 6))
                             for _ in range(rng.randint(1, 3)))
            body = " ".join(_camel_run(rng, rng.randint(3, 8))
                            for _ in range(rng.randint(2, 6)))
            body += " " + _sentence(rng, rng.randint(5, 20))
        elif i < 3000:
            # multi-byte unicode -> byte offsets differ from char offsets
            title = _uni_sentence(rng, rng.randint(3, 10))
            body = _uni_sentence(rng, rng.randint(30, 90))
        elif i < 4500:
            # long lines -> heavy regex work per document
            title = _sentence(rng, rng.randint(80, 200))
            body = _sentence(rng, rng.randint(300, 600))
        else:
            # punctuation heavy
            title = _punct_sentence(rng, rng.randint(4, 12))
            body = _punct_sentence(rng, rng.randint(20, 60))
        line = "{0}\t{1}\t{2}\t{3}\n".format(docid, url, title, body)
        b = line.encode("utf8")
        docids.append(docid)
        offsets.append(pos)
        pos += len(b)
        lines.append(b)
    return docids, offsets, lines


_DOCIDS, _OFFSETS, _LINES = _build_pool()

with open(_DOC_FILE, "wb") as _fh:
    _fh.write(b"".join(_LINES))


def _subset(indices):
    return {_DOCIDS[i]: _OFFSETS[i] for i in indices}


def _miss_dict():
    rng = random.Random(7)
    # only ascii lines, so a mid-line offset can never split a multibyte char
    pool_idx = list(range(0, 1500)) + list(range(4500, 6000))
    chosen = rng.sample(pool_idx, 2500)
    d = {}
    for i in chosen:
        if rng.random() < 0.35:
            j = chosen[rng.randrange(len(chosen))]
            off = _OFFSETS[j] + rng.randint(1, 30)   # wrong line / mid-line
        else:
            off = _OFFSETS[i]
        d[_DOCIDS[i]] = off
    return d


_MIXED_IDX = random.Random(11).sample(range(6000), 3000)

# pre-build every argument dict so each thunk is cheap
_D_CAMEL_1000 = _subset(range(0, 1000))
_D_UNICODE_1500 = _subset(range(1500, 3000))
_D_LONG_800 = _subset(range(3000, 3800))
_D_PUNCT_1500 = _subset(range(4500, 6000))
_D_MIXED_3000 = _subset(_MIXED_IDX)
_D_MISSES_2500 = _miss_dict()
_D_CAMEL_REV_1500 = _subset(list(range(1499, -1, -1)))
_D_LONG_1200 = _subset(range(3000, 4200))


def checks():
    return [
        ("empty", lambda: ({},)),
        ("single", lambda: ({_DOCIDS[0]: _OFFSETS[0]},)),
        ("bad-offset", lambda: ({"MISSING": 10 ** 9},)),
    ]


def cases():
    return [
        ("camel-1000", lambda: (_D_CAMEL_1000,)),
        ("unicode-1500", lambda: (_D_UNICODE_1500,)),
        ("long-800", lambda: (_D_LONG_800,)),
        ("punct-1500", lambda: (_D_PUNCT_1500,)),
        ("mixed-3000", lambda: (_D_MIXED_3000,)),
        ("misses-2500", lambda: (_D_MISSES_2500,)),
        ("camel-rev-1500", lambda: (_D_CAMEL_REV_1500,)),
        ("long-1200", lambda: (_D_LONG_1200,)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['mixed-3000', 'long-1200', 'long-800', 'unicode-1500']
_KEEP_CHECKS = ['empty', 'single', 'bad-offset']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
