# Inputs for text-search/python/convert-to-vespa-format.py::main, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import contextlib
import importlib
import io
import random
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Locate and import the repository module under test
# ---------------------------------------------------------------------------

def _find_module_dir():
    cwd = Path.cwd()
    cands = []
    for base in [cwd] + list(cwd.parents):
        cands.append(base / "text-search" / "python")
        cands.append(base / "sample-apps" / "text-search" / "python")
    for c in cands:
        if (c / "convert-to-vespa-format.py").is_file():
            return c
    for p in cwd.rglob("convert-to-vespa-format.py"):
        return p.parent
    raise RuntimeError("could not locate convert-to-vespa-format.py")


_MOD_DIR = _find_module_dir()
if str(_MOD_DIR) not in sys.path:
    sys.path.insert(0, str(_MOD_DIR))


def _import_under_test():
    """Import the module. Its top-level code may parse sys.argv, so feed it a
    plausible command line (the values are overwritten afterwards anyway)."""
    src = str(WORKDIR / "_argv_src")
    dst = str(WORKDIR / "_argv_dst")
    off = str(WORKDIR / "_argv_src" / "sample_offsets.tsv")
    candidates = [
        ["convert-to-vespa-format.py", src, dst, "docid,title,body", "doc", off],
        ["convert-to-vespa-format.py", src, dst, "docid,title,body", "doc"],
        ["convert-to-vespa-format.py", src, dst, "docid,title,body"],
        ["convert-to-vespa-format.py", src, dst],
    ]
    saved_argv = list(sys.argv)
    last_err = None
    try:
        for argv in candidates:
            sys.argv = argv
            try:
                with contextlib.redirect_stdout(io.StringIO()), \
                     contextlib.redirect_stderr(io.StringIO()):
                    return importlib.import_module("convert-to-vespa-format")
            except (SystemExit, IndexError, ValueError, TypeError) as exc:
                last_err = exc
        raise RuntimeError("failed to import convert-to-vespa-format: %r" % (last_err,))
    finally:
        sys.argv = saved_argv


_mod = _import_under_test()
main = _mod.main


# ---------------------------------------------------------------------------
# Helpers to build realistic data files
# ---------------------------------------------------------------------------

_ALPHA = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,-"


def _text(rng, n):
    if n <= 0:
        return ""
    return "".join(rng.choices(_ALPHA, k=n))


def _write_dataset(name, lines, offsets):
    d = WORKDIR / name
    d.mkdir(parents=True, exist_ok=True)
    docs_path = d / "docs.tsv"
    off_path = d / "sample_offsets.tsv"
    positions = []
    with open(docs_path, "wb") as f:
        for ln in lines:
            positions.append(f.tell())
            f.write((ln + "\n").encode("utf-8"))
    with open(off_path, "w", encoding="utf-8") as f:
        for key, idx in offsets:
            f.write("%s\t%d\n" % (key, positions[idx]))
    return d


def _build_case(name, n_docs, field_names, seed, title_len, body_len,
                bad_fields_every=0, bad_docid_every=0):
    rng = random.Random(seed)
    lines = []
    offsets = []
    for i in range(n_docs):
        docid = str(100000 + i)
        cols = [docid]
        for fi in range(1, len(field_names)):
            cols.append(_text(rng, title_len if fi == 1 else body_len))
        line = "\t".join(cols)
        if bad_fields_every and i % bad_fields_every == 0:
            line = "\t".join(cols[:-1])          # missing fields -> skipped
        if bad_docid_every and i % bad_docid_every == 0:
            line = "X" + line                    # wrong lookup value -> skipped
        offsets.append((docid, len(lines)))
        lines.append(line)
    src = _write_dataset("case_" + name, lines, offsets)
    outdir = WORKDIR / ("out_" + name)
    outdir.mkdir(parents=True, exist_ok=True)
    return src, outdir, list(field_names)


def _thunk(src, outdir, fields):
    def run():
        _mod.source_dir = str(src)
        _mod.dest_dir = str(outdir)
        _mod.docs_file = str(src / "docs.tsv")
        _mod.out_file = str(outdir / "documents.jsonl")
        _mod.sample_offset_file = str(src / "sample_offsets.tsv")
        _mod.fields = list(fields)
        _mod.doc_type = "doc"
        return ()
    return run


# ---------------------------------------------------------------------------
# Measured cases: 8 distinct workloads, built once at import time
# ---------------------------------------------------------------------------

_CASE_DEFS = [
    ("typical",      3000,  ["docid", "title", "body"],            0,  40,  250, 0, 0),
    ("large",        7000,  ["docid", "title", "body"],            1,  50,  300, 0, 0),
    ("long-body",    1500,  ["docid", "title", "body"],            2,  30, 1500, 0, 0),
    ("many-fields",  3000,  ["docid"] + ["f%d" % i for i in range(1, 9)], 3, 40, 40, 0, 0),
    ("with-skips",   5000,  ["docid", "title", "body"],            4,  40,  200, 3, 5),
    ("tiny-lines",  12000,  ["docid", "title"],                    5,   8,    0, 0, 0),
    ("long-titles",  4000,  ["docid", "title", "body"],            6, 500,  100, 0, 0),
    ("single-field",15000,  ["docid"],                             7,   0,    0, 0, 0),
]

_BUILT = [(name, _thunk(*_build_case(name, *rest))) for name, *rest in _CASE_DEFS]


def cases():
    return [(name, thunk) for name, thunk in _BUILT]


# ---------------------------------------------------------------------------
# Edge cases (never measured)
# ---------------------------------------------------------------------------

def _edge(name, docs_bytes, offsets_bytes, fields):
    src = WORKDIR / ("chk_" + name)
    src.mkdir(parents=True, exist_ok=True)
    outdir = WORKDIR / ("chk_out_" + name)
    outdir.mkdir(parents=True, exist_ok=True)

    def run():
        (src / "docs.tsv").write_bytes(docs_bytes)
        (src / "sample_offsets.tsv").write_bytes(offsets_bytes)
        _mod.source_dir = str(src)
        _mod.dest_dir = str(outdir)
        _mod.docs_file = str(src / "docs.tsv")
        _mod.out_file = str(outdir / "documents.jsonl")
        _mod.sample_offset_file = str(src / "sample_offsets.tsv")
        _mod.fields = list(fields)
        _mod.doc_type = "doc"
        return ()
    return run


def checks():
    return [
        ("empty", _edge("empty", b"", b"", ["docid", "title", "body"])),
        ("one-doc", _edge("one",
                          b"100000\thello\tworld\n",
                          b"100000\t0\n",
                          ["docid", "title", "body"])),
        ("offset-past-eof", _edge("past",
                                  b"100000\thello\tworld\n",
                                  b"999999\t100000\n",
                                  ["docid", "title", "body"])),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['single-field', 'tiny-lines', 'large', 'long-titles']
_KEEP_CHECKS = ['empty', 'one-doc', 'offset-past-eof']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
