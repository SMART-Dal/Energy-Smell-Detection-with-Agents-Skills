#!/usr/bin/env python3
"""Generate the measured inputs for one unit with an LLM, and keep only what runs.

    <the repository's venv python> generate.py REPO UNIT OUT_DIR --key FILE [--cache DIR]

The agent never writes the inputs its repairs are measured on: it could tune
them to the repair, and in the first pilots three of nine submissions replaced
the code they were meant to exercise. This writes them instead, adapting two
published methods to a setting with no reference repair:

  * GSO (Shetty et al., 2025): an LLM writes a performance test from the
    repository's own code -- here the unit, its class, what it uses and where
    the repository calls it -- split into untimed setup and a timed call, and
    a candidate is kept only if it executes (execution-based rejection
    sampling). GSO keeps tests on which a known developer optimization is
    faster; there is no such repair here, so a candidate is kept if it runs on
    the original code and gives the same output on a second, fresh run.
  * COFFE / STGen (Peng et al., 2025): ask for stressful, diverse inputs, more
    than needed, and keep the most expensive. Eight are asked for and the four
    slowest that pass are kept.

Behaviour is checked later, by verify.py, as output equivalence between the
original and the repair -- GSO's `check_equivalence`, without hand-written
assertions.

At most two calls per unit. Both reason. The second sees what failed and on
which line of its source -- or, when the first produced no code (out of time,
or an empty answer after thinking), that call's reasoning as notes to write
from. Run under the repository's venv python: the candidates are executed in
it, exactly as verify.py will execute them.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import sys
import threading
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lib.inputs import file_name  # noqa: E402

MODEL = "deepseek/deepseek-v4.1-flash"
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
EFFORT = "medium"
CALL_TIMEOUT_S = 150       # one call, reasoning included; a cut-off call is billed in full
MAX_TOKENS = 32000         # reasoning and answer together
ROUNDS = 2
CANDIDATES = 8
KEEP = 4                   # every unit is measured on exactly four inputs
MAX_CALL_S = 1.0           # one call on the original; slower inputs are dropped
VALIDATE_BUDGET_S = 180    # pass 1, every input of one source, restarts included
CONFIRM_BUDGET_S = 90      # pass 2, the second runs of the inputs that will be kept
CASE_DEADLINE_S = 20       # building, running and timing one input
OPEN_DEADLINE_S = 60       # loading the unit and the inputs' module-level code
SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "site-packages", "__pycache__"}
VALIDATION_SLOTS = None
"""A semaphore bounding how many units execute candidates at once; the service sets it."""

SYSTEM = """You are a performance testing expert. You will write the inputs for an energy measurement of one Python function from a real repository. We run the original function and a modified version of it on your inputs, each input many times in a row, and compare their energy use and their outputs.

# What to write
Python source defining two functions, `checks()` and `cases()`. Each returns a list of `(label, thunk)` pairs with distinct labels. A thunk takes no arguments and returns a tuple of positional arguments for the function, e.g. `lambda: (rows, 3)`. For keyword arguments the thunk returns `call(...)`, e.g. `lambda: call(rows, sep=",")`; `call` is provided, do not import or define it. A method is called as a plain function: the thunk builds the instance and passes it as the first argument.
**The thunk returns the arguments; it never calls the function under test.** We call the function with them, and time only that call.

# Instructions
1. **Setup is never timed**: everything that builds data, objects or files goes in the thunk or in module-level code. Thunks run before the timing starts; only the call of the function is timed.

2. **`cases()`: exactly 8 measured inputs.** We run them on the original function and keep the 4 that do the most work.
    - Define a real workload: the kind of data this function gets in this repository (see where the repository calls it). Use realistic scale and complexity, and a fixed random seed (`random.Random(0)`) when generating data.
    - Generate stressful inputs: complex, time-consuming, as diverse as possible. Each case should make the function do substantial and different work: different paths through its code, sizes, data distributions, hit and miss ratios, duplicates, lengths.
    - Avoid uniformity or patterns (repeating, sorted, same values) that a simple trick could exploit, unless that pattern is what the repository really passes.
    - One call should take roughly 1 ms to 200 ms on the original. Inputs where one call takes over 1 s are dropped. Keep the data in memory under about 100 MB, and building all inputs under about 10 s.
    - The function's output is compared in full after every input, so keep what it returns (and anything it writes) under about 100 000 values. Its arguments are rendered before and after each call to see whether it changed them, so keep each input's data under about 1 000 000 values.
    - Every case must run to completion on the original function without raising.

3. **`checks()`: 2 or 3 small edge inputs** (empty, one element, None, an odd type) checked only for identical behaviour, never measured. These may raise.

4. **Build real inputs; never replace code.** No mocks, no monkeypatching, no `unittest.mock`, no assigning functions or lambdas to attributes, of the repository or of a library. Setting data (a module's configuration, an object's fields) to build an input is fine. No network access, no subprocesses. Do not fake the environment either: no stand-in programs on `PATH`, no fake system files.
    - Module globals the function reads must be set on the repository's own module (`import pricing; pricing.args = ...`, `hyperlink.slugs.update(...)`); a variable of the same name in your source is a different variable and the function never sees it.
    - Prepare the way the repository's own callers do: if a caller runs some setup before calling the function (adds a path, loads a config), do the same in the thunk.

5. **Files**: if the function reads files, create them under `WORKDIR` (a provided `pathlib.Path`; do not define it), in module-level code or in the thunk. Anything the function writes must go under `WORKDIR` too.

6. **Same work on every call**: the call is repeated hundreds of times with the same input. Anything the function changes outside its arguments (a class attribute, a module global, a cache, a file) carries over from one call to the next, so if it caches or records what it has seen, give every thunk call new keys (e.g. with `itertools.count()`), so every call takes the same path. If it creates files, have the thunk remove them first. No time-dependent or unseeded random behaviour.

7. Import the repository's modules exactly as shown in the task. Use only the standard library, the repository itself and packages the repository already imports.

8. **If the function cannot run here at all** -- it needs network access, a remote service, credentials, special hardware, or a library that is not available -- and no input could avoid that, do not write code: reply with one line `CANNOT RUN: <the reason>`.

Decide on the inputs and write the code: simple inputs that run are better than clever ones that do not.

# Output format
Exactly one ```python block holding the complete source. An example for a function `summarize(rows, top=10)`:
```python
import random

def _rows(n, columns, seed):
    rng = random.Random(seed)
    return [{f"c{j}": rng.randint(0, 10**6) for j in range(columns)} for _ in range(n)]

def checks():
    return [
        ("empty",      lambda: ([],)),                            # summarize([])
        ("none-value", lambda: ([{"c0": None}],)),
    ]

def cases():
    return [
        ("typical",    lambda: (_rows(2_000, 4, 0),)),            # summarize(rows)
        ("top-100",    lambda: call(_rows(5_000, 4, 1), top=100)), # summarize(rows, top=100)
        # ... 8 in total
    ]
```
For a method such as `Report.render(self, top)`, the thunk builds the instance: `lambda: (Report(_rows(500, 4, 2)), 10)`.
"""

FEEDBACK = """We ran your inputs on the original function. Only {ok} of the {total} measured inputs can be used; we need at least {need}.

{details}

Fix the failing inputs (or replace them with new ones) and return the complete source again, with exactly 8 measured inputs in `cases()`. Same rules as before."""

NOTES = """

## Your notes from an earlier attempt (it ran out of time before writing the code)
{notes}

Write the code now, following the notes where they are right."""


# ---------------------------------------------------------------- storage

class Store:
    """A directory written through a descriptor opened up front.

    The harness locks the directory above (`chmod 000 ~/energy-exp`) while the
    agent runs; a descriptor opened before that still reaches what is under it,
    so the cache and our copy of the inputs stay where the agent cannot.
    """

    def __init__(self, path: Path):
        Path(path).mkdir(parents=True, exist_ok=True)
        self.path = Path(path)
        self.fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        self._lock = threading.Lock()

    def _parent(self, rel: str, create: bool) -> tuple[int, str, list[int]]:
        parts = rel.split("/")
        fd, opened = self.fd, []
        for part in parts[:-1]:
            if create:
                try:
                    os.mkdir(part, 0o755, dir_fd=fd)
                except FileExistsError:
                    pass
            fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY, dir_fd=fd)
            opened.append(fd)
        return fd, parts[-1], opened

    def write(self, rel: str, text: str) -> None:
        with self._lock:
            fd, name, opened = self._parent(rel, create=True)
            try:
                tmp = f".{name}.tmp"
                handle = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644, dir_fd=fd)
                with os.fdopen(handle, "w") as out:
                    out.write(text)
                os.replace(tmp, name, src_dir_fd=fd, dst_dir_fd=fd)
            finally:
                for o in opened:
                    os.close(o)

    def read(self, rel: str) -> str | None:
        try:
            fd, name, opened = self._parent(rel, create=False)
        except OSError:
            return None
        try:
            handle = os.open(name, os.O_RDONLY, dir_fd=fd)
            with os.fdopen(handle) as f:
                return f.read()
        except OSError:
            return None
        finally:
            for o in opened:
                os.close(o)


def cache_key(root: Path, repo_name: str, unit: str) -> str:
    """Per repository, unit and the content of the unit's file: an edited file is a new key."""
    path, _ = unit.split("::", 1)
    digest = hashlib.sha256((root / path).read_bytes()).hexdigest()[:16]
    return f"{repo_name}/{file_name(unit)[:-3]}-{digest}"


# ---------------------------------------------------------------- context

def import_name(root: Path, path: str) -> str:
    """Same rule as the worker's `_import_name`: package name, or the script's file name."""
    parts = list(Path(path).with_suffix("").parts)
    dirs, leaf = parts[:-1], ([] if parts[-1] == "__init__" else parts[-1:])
    depth = 0
    while depth < len(dirs) and Path(root, *dirs[:len(dirs) - depth], "__init__.py").is_file():
        depth += 1
    return ".".join(dirs[len(dirs) - depth:] + leaf) or ".".join(parts)


def import_root(root: Path, path: str) -> Path:
    """The directory the module's own absolute imports resolve from."""
    parts = list(Path(path).parts[:-1])
    depth = 0
    while depth < len(parts) and Path(root, *parts[:len(parts) - depth], "__init__.py").is_file():
        depth += 1
    return Path(root, *parts[:len(parts) - depth])


def find_node(tree: ast.Module, qualname: str):
    node, owner = tree, None
    for part in qualname.split("."):
        owner = node
        node = next((c for c in node.body if isinstance(
            c, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and c.name == part), None)
        if node is None:
            raise KeyError(qualname)
    return node, owner


def src(lines: list[str], node) -> str:
    first = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
    return "".join(lines[first - 1:node.end_lineno])


def cap(text: str, max_lines: int) -> str:
    rows = text.splitlines(keepends=True)
    return text if len(rows) <= max_lines else "".join(rows[:max_lines]) + "    # ... (truncated)\n"


def class_outline(lines: list[str], cls: ast.ClassDef, full: set[str]) -> str:
    """The class with every method body elided except the ones named in `full`."""
    out = [src(lines, cls).splitlines(keepends=True)[0]]
    for child in cls.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if child.name in full:
                out.append(src(lines, child))
            else:
                first = min([child.lineno] + [d.lineno for d in child.decorator_list])
                header_end = child.body[0].lineno - 1
                if isinstance(child.body[0], ast.Expr) and isinstance(
                        getattr(child.body[0], "value", None), ast.Constant):
                    header_end = child.body[0].end_lineno      # keep the docstring
                head = "".join(lines[first - 1:max(header_end, child.lineno)])
                out.append(head + " " * (child.col_offset + 4) + "...\n")
        else:
            out.append(src(lines, child))
    return "".join(out)


def signature(lines: list[str], node) -> str:
    """A def's header and the first line of its docstring; a class's header,
    its short fields and its public method headers."""
    def head(fn) -> str:
        first = min([fn.lineno] + [d.lineno for d in fn.decorator_list])
        text = "".join(lines[first - 1:fn.body[0].lineno - 1]).rstrip()
        doc = ast.get_docstring(fn)
        if doc:
            text += "\n" + " " * (fn.col_offset + 4) + '"""' + doc.strip().splitlines()[0][:150] + '"""'
        return text + "\n" + " " * (fn.col_offset + 4) + "...\n"
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return head(node)
    out = ["".join(lines[node.lineno - 1:node.body[0].lineno - 1])]
    for child in node.body:
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                not child.name.startswith("_") or child.name in ("__init__", "__post_init__")):
            out.append(head(child))
        elif isinstance(child, (ast.AnnAssign, ast.Assign)) and child.end_lineno - child.lineno < 3:
            out.append("".join(lines[child.lineno - 1:child.end_lineno]))
    return cap("".join(out), 40)


def imported_signatures(root: Path, path: str, tree: ast.Module, used: set[str],
                        budget: int = 160) -> list[str]:
    """Signatures of what the module imports from the repository's own modules,
    the names the unit uses first: where a model would otherwise guess them."""
    base, here = import_root(root, path), (root / path).parent
    found = []
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom):
            continue
        start = here if node.level else base
        for _ in range(max(node.level - 1, 0)):
            start = start.parent
        target = start.joinpath(*node.module.split(".")) if node.module else start
        file = target.with_suffix(".py") if target.with_suffix(".py").is_file() else target / "__init__.py"
        if not file.is_file() or not str(file.resolve()).startswith(str(root.resolve())):
            continue
        try:
            text = file.read_text(errors="replace")
            other = ast.parse(text)
        except (OSError, SyntaxError, ValueError):
            continue
        rows = text.splitlines(keepends=True)
        defs = {n.name: n for n in other.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
        for alias in node.names:
            if alias.name in defs:
                found.append(((alias.asname or alias.name) not in used,
                              f"# from {'.' * node.level}{node.module or ''} import {alias.name}\n"
                              + signature(rows, defs[alias.name])))
    out = []
    for _, text in sorted(found, key=lambda f: f[0]):
        budget -= text.count("\n")
        if budget < 0:
            break
        out.append(text)
    return out


def call_sites(root: Path, path: str, qualname: str, unit_lines: range,
               limit: int = 6) -> list[str]:
    """Real calls of the unit, found in the syntax tree rather than by name.

    A top-level function counts where it is called by a name the file imported
    from the unit's module (or in its own file), or as `module.function(...)`;
    a method counts as `.method(...)` anywhere, and its class's constructor as
    `Class(...)`. A text search matched docstrings and every `.plan(` of every
    other class, and crowded out the one call that showed how to prepare it.
    """
    parts = qualname.split(".")
    method = len(parts) > 1
    name, owner = parts[-1], (parts[-2] if method else None)
    module_leaf = Path(path).stem
    hits = []
    for file in sorted(root.rglob("*.py")):
        rel = file.relative_to(root)
        if SKIP_DIRS & set(rel.parts):
            continue
        try:
            text = file.read_text(errors="replace")
            if name not in text and (owner or "\0") not in text:
                continue
            tree = ast.parse(text)
        except (OSError, SyntaxError, ValueError):
            continue
        same_file = str(rel) == path
        local_names, module_aliases = set(), set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                from_leaf = (node.module or "").split(".")[-1]
                for alias in node.names:
                    if from_leaf == module_leaf and alias.name in (name, owner):
                        local_names.add(alias.asname or alias.name)
                    if alias.name == module_leaf:
                        module_aliases.add(alias.asname or alias.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[-1] == module_leaf:
                        module_aliases.add(alias.asname or alias.name.split(".")[0])
        if same_file:
            local_names |= {name, owner} - {None}
        rows = text.splitlines()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func, target = node.func, None
            if isinstance(func, ast.Name) and func.id in local_names:
                target = func.id
            elif isinstance(func, ast.Attribute):
                if method and func.attr == name:
                    target = name
                elif func.attr in (name, owner) and isinstance(func.value, ast.Name) \
                        and func.value.id in module_aliases:
                    target = func.attr
            if target is None or (method and target == name and not isinstance(func, ast.Attribute)
                                  and not same_file):
                continue
            i = node.lineno - 1
            if same_file and i in unit_lines:
                continue
            lo, hi = max(0, i - 4), min(len(rows), node.end_lineno + 3)
            hits.append(("test" not in str(rel).lower(), same_file, str(rel), i + 1,
                         "\n".join(rows[lo:hi])))
    hits.sort(key=lambda h: (h[0], h[1]))
    out, per_file = [], {}
    for _, _, rel, line, snippet in hits:
        if per_file.get(rel, 0) >= 2:
            continue
        per_file[rel] = per_file.get(rel, 0) + 1
        out.append(f"# {rel}:{line}\n{snippet}")
        if len(out) >= limit:
            break
    return out


def build_context(root: Path, unit: str) -> str:
    """The user message: the unit and what a model needs to build real inputs for it."""
    path, qualname = unit.split("::")
    text = (root / path).read_text(errors="replace")
    lines = text.splitlines(keepends=True)
    tree = ast.parse(text)
    node, owner = find_node(tree, qualname)
    module = import_name(root, path)
    parts = qualname.split(".")
    if all(p.isidentifier() for p in module.split(".")):
        how = f"`from {module} import {parts[0]}`"
    else:
        how = (f"`{parts[0]} = importlib.import_module({module!r}).{parts[0]}` "
               f"(the file name is not an identifier)")
    if len(parts) > 1:
        how += f"; the method is called as `{qualname}(instance, ...)`"

    sections = [f"Repository: {root.name}",
                f"Function under test: `{qualname}` in `{path}`",
                f"Import it as {how}.",
                f"\n## The function\n```python\n{cap(src(lines, node), 200)}```"]
    if isinstance(owner, ast.ClassDef):
        outline = class_outline(lines, owner, {"__init__", "__post_init__", node.name})
        sections.append(f"\n## Its class (other method bodies elided)\n```python\n{cap(outline, 200)}```")
    imports = [src(lines, n) for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    if imports:
        sections.append("\n## Imports of its module\n```python\n" + cap("".join(imports), 40) + "```")

    used = {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}
    used |= {n.attr for n in ast.walk(node) if isinstance(n, ast.Attribute)}
    defs, budget = [], 250
    for child in tree.body:
        name = None
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = child.name
        elif isinstance(child, (ast.Assign, ast.AnnAssign)):
            targets = child.targets if isinstance(child, ast.Assign) else [child.target]
            name = next((t.id for t in targets if isinstance(t, ast.Name) and t.id in used), None)
        if not name or name not in used or child is node or child is owner:
            continue
        body = cap(class_outline(lines, child, {"__init__"}) if isinstance(child, ast.ClassDef)
                   else src(lines, child), 60)
        budget -= body.count("\n")
        if budget < 0:
            break
        defs.append(body)
    # Globals the module sets somewhere other than its top level: `global args`
    # inside a setup function, or an assignment under `if __name__ == ...`.
    top = {c.name for c in tree.body if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef,
                                                        ast.ClassDef))}
    top |= {t.id for c in tree.body if isinstance(c, ast.Assign) for t in c.targets
            if isinstance(t, ast.Name)}
    elsewhere = used - top - set(dir(__builtins__))
    for child in tree.body:
        if budget < 0 or child is node or child is owner:
            continue
        sets = set()
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            sets = {n for g in ast.walk(child) if isinstance(g, ast.Global) for n in g.names}
        elif isinstance(child, (ast.If, ast.Try, ast.With)):
            sets = {t.id for a in ast.walk(child) if isinstance(a, ast.Assign)
                    for t in a.targets if isinstance(t, ast.Name)}
        if sets & elsewhere:
            body = cap(src(lines, child), 60)
            budget -= body.count("\n")
            defs.append(body)
    if defs:
        sections.append("\n## Definitions it uses from the same module\n```python\n"
                        + "\n".join(defs) + "```")
    sigs = imported_signatures(root, path, tree, used)
    if sigs:
        sections.append("\n## Signatures of what its module imports from the repository\n"
                        "```python\n" + "\n".join(sigs) + "```")
    sites = call_sites(root, path, qualname, range(node.lineno - 1, node.end_lineno))
    if sites:
        sections.append("\n## Where the repository calls it or builds its class\n```python\n"
                        + "\n\n".join(sites) + "\n```")
    else:
        sections.append("\n## Where the repository calls it\nNo call sites found.")
    sections.append(f"\nWrite `checks()` and `cases()` for `{qualname}`. Remember: setup "
                    f"in the thunk or at module level, never timed.")
    return "\n".join(sections)


# -------------------------------------------------------------------- LLM

def ask_llm(messages: list[dict], key: str) -> dict:
    """One streamed call, cut off at CALL_TIMEOUT_S. What it said, thought and cost."""
    body = {"model": MODEL, "messages": messages, "max_tokens": MAX_TOKENS, "stream": True,
            "reasoning": {"effort": EFFORT}, "usage": {"include": True}, "temperature": 0.7,
            "provider": {"sort": "throughput"}}
    request = urllib.request.Request(
        ENDPOINT, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    start = time.monotonic()
    content: list[str] = []
    thought: list[str] = []
    usage, finish, provider = {}, None, None

    def partial(error: str) -> dict:
        return {"error": error, "seconds": round(time.monotonic() - start, 1),
                "content": "".join(content), "reasoning": "".join(thought)}
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            for raw in response:
                if time.monotonic() - start > CALL_TIMEOUT_S:
                    return partial(f"timed out after {CALL_TIMEOUT_S}s")
                line = raw.decode(errors="replace").strip()
                if not line.startswith("data: ") or line == "data: [DONE]":
                    continue
                chunk = json.loads(line[6:])
                if "error" in chunk:
                    return partial(json.dumps(chunk["error"])[:300])
                provider = chunk.get("provider") or provider
                usage = chunk.get("usage") or usage
                for choice in chunk.get("choices") or []:
                    delta = choice.get("delta") or {}
                    thought.append(delta.get("reasoning") or "")
                    content.append(delta.get("content") or "")
                    finish = choice.get("finish_reason") or finish
    except Exception as exc:  # noqa: BLE001 -- network, HTTP, a broken stream: all a failed call
        return partial(f"{type(exc).__name__}: {str(exc)[:300]}")
    return {"content": "".join(content), "reasoning": "".join(thought),
            "seconds": round(time.monotonic() - start, 1), "finish": finish,
            "provider": provider, "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "reasoning_tokens": (usage.get("completion_tokens_details") or {}).get("reasoning_tokens"),
            "cost": usage.get("cost")}


def extract_source(content: str) -> str | None:
    blocks = re.findall(r"```python\s*\n(.*?)```", content, re.S)
    return blocks[-1] if blocks else None


# ------------------------------------------------------------- validation

_ENVIRONMENT = re.compile(r"environ\s*(\[\s*['\"]PATH|\.update|\.setdefault\s*\(\s*['\"]PATH)|putenv")


def validate(root: Path, unit: str, source: str, work: Path) -> dict:
    """Run the candidates on the original, the way verify.py will run them.

    Pass 1, every input: it runs without raising, and how long one call takes.
    Pass 2, the most expensive first: a second run on fresh inputs gives the
    same output, compared as verify.py compares the two versions -- the value,
    what it printed, the files it wrote, and its effect on its arguments (not
    the arguments themselves, which may carry a construction timestamp).
    Stops once KEEP have passed: rendering a large argument twice more for an
    input that will not be kept is most of the cost.
    """
    from lib.pair import LoadError, Pair, WorkerError, stage
    from lib.submission import replaced_code

    problem = replaced_code(source)
    if not problem and _ENVIRONMENT.search(source):
        problem = ("it changes the environment (PATH); a stand-in program replaces code "
                   "just as a mock does")
    if problem:
        return {"fatal": f"refused: {problem}", "cases": [], "checks": []}
    work = work.resolve()
    before, after = stage(root.resolve(), {}, work)
    trace: dict = {}

    class TracedPair(Pair):
        """Keeps the worker's last reply: its traceback says which line of the source failed."""

        def _send(self, payload):
            trace["proc"] = self.process
            super()._send(payload)

        def _receive(self):
            answer = super()._receive()
            trace["answer"] = answer
            return answer

    def where() -> str:
        found = re.findall(r'File "<cases_source>", line (\d+)',
                           (trace.get("answer") or {}).get("error") or "")
        rows = source.splitlines()
        if not found or int(found[-1]) > len(rows):
            return ""
        n = int(found[-1])
        return f" (at line {n} of your source: `{rows[n - 1].strip()[:160]}`)"

    def open_pair():
        trace.clear()
        killed = []
        timer = threading.Timer(OPEN_DEADLINE_S, lambda: (killed.append(1), trace["proc"].kill())
                                if trace.get("proc") else None)
        timer.start()
        try:
            return TracedPair(before, after, unit, source, work, meter="auto")
        except LoadError as exc:
            if killed:
                raise LoadError("before", "cases", f"loading took over {OPEN_DEADLINE_S}s "
                                "(module-level code builds too much)") from exc
            raise
        finally:
            timer.cancel()

    try:
        pair = open_pair()
    except LoadError as exc:
        if exc.stage == "import":
            # The unit's own module, before any input runs: no input can fix it.
            return {"fatal": f"the unit's module does not load here: {exc}", "environment": True,
                    "cases": [], "checks": []}
        return {"fatal": f"the source does not load ({exc.stage}): {exc}{where()}",
                "cases": [], "checks": []}
    labels, check_labels = list(pair.labels), list(pair.check_labels)

    def guarded(fn):
        """fn(pair) with a deadline; on a timeout the worker is killed and reopened."""
        nonlocal pair
        timer = threading.Timer(CASE_DEADLINE_S, pair.process.kill)
        timer.start()
        try:
            return fn(pair), None
        except WorkerError as exc:
            if pair.process.poll() is not None:
                timed_out = not timer.is_alive()
                pair.close()
                pair = open_pair()
                return None, (f"took over {CASE_DEADLINE_S}s" if timed_out
                              else f"the worker died: {exc}")
            return None, str(exc) + where()
        finally:
            timer.cancel()

    started = time.monotonic()

    def out_of_time() -> bool:
        return time.monotonic() - started > VALIDATE_BUDGET_S

    results, candidates, firsts = {}, [], {}
    for i, label in enumerate(labels):
        if out_of_time():
            results[label] = {"label": label, "ok": False, "why": "not checked: the inputs "
                              f"before it used up the {VALIDATE_BUDGET_S}s for checking them all"}
            continue
        first, err = guarded(lambda p: p.side("before").ask(op="check", set="cases", index=i))
        if err:
            results[label] = {"label": label, "ok": False, "why": f"building or running it failed: {err}"}
            continue
        if first["kind"] == "raise":
            results[label] = {"label": label, "ok": False,
                              "why": f"the original raises {first.get('message') or first['raised']}"}
            continue
        timed, err = guarded(lambda p: p.side("before").ask(op="time", index=i, calls=3))
        if err:
            results[label] = {"label": label, "ok": False, "why": f"timing failed: {err}"}
            continue
        if timed["seconds"] > MAX_CALL_S:
            results[label] = {"label": label, "ok": False, "seconds": timed["seconds"],
                              "why": f"one call takes {timed['seconds']:.2f}s (limit {MAX_CALL_S}s)"}
            continue
        candidates.append((timed["seconds"], i, label))
        firsts[label] = first

    passed = 0
    confirming = time.monotonic()
    for seconds, i, label in sorted(candidates, reverse=True):
        if passed >= KEEP:
            results[label] = {"label": label, "ok": False, "seconds": seconds, "spare": True,
                              "why": f"not needed: {KEEP} more expensive inputs passed"}
            continue
        if time.monotonic() - confirming > CONFIRM_BUDGET_S:
            results[label] = {"label": label, "ok": False, "why": "not checked: out of time"}
            continue
        first = firsts[label]
        second, err = guarded(lambda p: p.side("before").ask(op="check", set="cases", index=i))
        if err or second["kind"] != "return":
            results[label] = {"label": label, "ok": False, "why": "second run failed: "
                              + (err or second.get("message") or second["raised"])}
            continue
        differ = [k for k in ("value", "stdout", "files") if first[k] != second[k]]
        if first["mutates"] != second["mutates"] or (
                first["mutates"] and first["args_before"] == second["args_before"]
                and first["args"] != second["args"]):
            differ.append("args")
        if differ:
            results[label] = {"label": label, "ok": False,
                              "why": "two runs on fresh inputs gave different output: "
                                     + first_difference(differ[0], first[differ[0]], second[differ[0]])}
            continue
        results[label] = {"label": label, "ok": True, "seconds": seconds}
        passed += 1

    checks = []
    checking = time.monotonic()
    for j, label in enumerate(check_labels):
        if time.monotonic() - checking > 60:
            checks.append({"label": label, "ok": False, "kind": None, "why": "not checked: out of time"})
            continue
        out, err = guarded(lambda p: p.side("before").ask(op="check", set="checks", index=j))
        checks.append({"label": label, "ok": err is None,
                       "kind": out["kind"] if out else None, "why": err})
    pair.close()
    return {"fatal": None, "cases": [results[label] for label in labels], "checks": checks}


def first_difference(channel: str, a, b) -> str:
    """Where two renderings of one channel first part, in a few words."""
    what = {"value": "the return value", "stdout": "what it printed",
            "args": "its arguments after the call", "files": "the files it wrote"}[channel]
    a, b = str(a), str(b)
    i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
    lo = max(0, i - 60)
    return f"{what} differs; first run ...{a[lo:i + 80]!r}..., second run ...{b[lo:i + 80]!r}..."


def usable(v: dict) -> list[dict]:
    return [c for c in v["cases"] if c["ok"]]


def succeeded(v: dict) -> bool:
    return len(usable(v)) >= KEEP and any(c["ok"] for c in v.get("checks") or [])


def feedback(v: dict) -> str:
    if v["fatal"]:
        details, ok, total = v["fatal"], 0, CANDIDATES
    else:
        rows = [f"- {c['label']}: " + ("ok" if c["ok"] else c["why"]) for c in v["cases"]]
        if not any(c["ok"] for c in v.get("checks") or []):
            rows.append("- checks(): none of the edge inputs could be built or run: "
                        + "; ".join(f"{c['label']}: {c['why']}" for c in v.get("checks") or [])
                        + " (they may raise inside the function, but building them must work)")
        details, ok, total = "\n".join(rows), len(usable(v)), len(v["cases"])
    if "TypeError" in details:
        details += ("\n\nA TypeError usually means the thunk does not return the function's "
                    "arguments: it returns them as a tuple, or `call(...)` for keyword "
                    "arguments, and never calls the function itself.")
    return FEEDBACK.format(ok=ok, total=total, need=KEEP, details=details)


def why_failed(v: dict | None, calls: list[dict]) -> str:
    """One sentence for the agent, which records the unit's suspicions as blocked with it."""
    if v is None:
        errors = "; ".join(c["error"] for c in calls if c.get("error")) or "no usable answer"
        return f"the generator produced no inputs ({errors})"
    if v.get("environment"):
        return v["fatal"][:400]
    if v["fatal"]:
        return f"the generated inputs could not be used: {v['fatal'][:300]}"
    whys = [c["why"] for c in v["cases"] if not c["ok"]]
    common = max(set(whys), key=whys.count) if whys else ""
    return (f"only {len(usable(v))} of {len(v['cases'])} generated inputs ran and repeated "
            f"on the original code (most often: {common[:300]})")


def final_source(source: str, keep: list[str], checks: list[str], unit: str) -> str:
    return (f"# Inputs for {unit}, generated outside the session: the {KEEP} most\n"
            f"# expensive of {CANDIDATES} candidates that ran and repeated on the original.\n\n"
            + source.rstrip() + "\n\n\n# ---- the selection\n"
            "_generated_cases, _generated_checks = cases, checks\n"
            f"_KEEP = {keep!r}\n_KEEP_CHECKS = {checks!r}\n\n\n"
            "def cases():\n    return [c for c in _generated_cases() if c[0] in _KEEP]\n\n\n"
            "def checks():\n    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]\n")


# ---------------------------------------------------------------- the unit

@dataclass
class Outcome:
    unit: str
    ready: bool
    source: str | None = None
    reason: str = ""
    report: dict = field(default_factory=dict)


def generate(root: Path, unit: str, work: Path, key: str, record=None) -> Outcome:
    """Up to ROUNDS calls for one unit. `record(name, text)` receives every artifact."""
    record = record or (lambda *_: None)
    started = time.monotonic()
    context = build_context(root, unit)
    record("prompt.md", SYSTEM + "\n\n=== USER ===\n\n" + context)
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": context}]
    report: dict = {"unit": unit, "model": MODEL, "calls": [], "rounds": []}
    best = last = None
    cannot = None
    for round_no in range(1, ROUNDS + 1):
        reply = ask_llm(messages, key)
        report["calls"].append({k: v for k, v in reply.items() if k not in ("content", "reasoning")})
        record(f"reasoning_{round_no}.md", reply.get("reasoning") or "")
        record(f"reply_{round_no}.md", reply.get("content") or reply.get("error", ""))
        code = extract_source(reply.get("content") or "") if not reply.get("error") else None
        said = re.search(r"^\s*CANNOT RUN:\s*(.+)$", reply.get("content") or "", re.M)
        if said and not (code and "def cases" in code):
            cannot = said.group(1).strip()
            report["rounds"].append({"fatal": "CANNOT RUN: " + cannot})
            break
        if code is None:
            v = None
            report["rounds"].append({"fatal": reply.get("error") or "no ```python block in the reply"})
        else:
            record(f"source_{round_no}.py", code)
            slots = VALIDATION_SLOTS
            if slots:
                slots.acquire()
            try:
                t0 = time.monotonic()
                v = validate(root, unit, code, work / f"round_{round_no}")
                v["validate_s"] = round(time.monotonic() - t0, 1)
            finally:
                if slots:
                    slots.release()
            report["rounds"].append({k: v.get(k) for k in ("fatal", "cases", "checks", "validate_s")})
            last = v
            if best is None or len(usable(v)) > len(usable(best[1])):
                best = (code, v)
            if succeeded(v) or v.get("environment"):
                break
        if round_no == ROUNDS:
            break
        if code is not None:
            messages += [{"role": "assistant", "content": reply["content"]},
                         {"role": "user", "content": feedback(v)}]
        else:
            notes = (reply.get("reasoning") or "")[:60000]
            messages = [{"role": "system", "content": SYSTEM},
                        {"role": "user", "content": context + (NOTES.format(notes=notes) if notes else "")}]

    report["seconds"] = round(time.monotonic() - started, 1)
    report["cost"] = round(sum(c.get("cost") or 0 for c in report["calls"]), 5)
    if best and succeeded(best[1]):
        ranked = sorted(usable(best[1]), key=lambda c: -c["seconds"])[:KEEP]
        report["kept"] = [[c["label"], round(c["seconds"] * 1000, 3)] for c in ranked]
        source = final_source(best[0], [c["label"] for c in ranked],
                              [c["label"] for c in best[1]["checks"] if c["ok"]], unit)
        return Outcome(unit, True, source, "", report)
    report["kept"] = []
    reason = f"it cannot run here: {cannot}" if cannot else why_failed(last, report["calls"])
    report["reason"] = reason
    return Outcome(unit, False, None, reason, report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("repo", type=Path, help="a pristine copy of the repository")
    parser.add_argument("unit", help="path::qualname")
    parser.add_argument("out", type=Path, help="where the prompt, replies and inputs go")
    parser.add_argument("--key", type=Path, required=True, help="file holding the OpenRouter key")
    parser.add_argument("--cache", type=Path, help="reuse and record successful generations here")
    args = parser.parse_args()
    out = Store(args.out)
    cache = Store(args.cache) if args.cache else None
    ckey = cache_key(args.repo, args.repo.name, args.unit) if cache else None
    if cache and cache.read(f"{ckey}/cases.py"):
        out.write("cases.py", cache.read(f"{ckey}/cases.py"))
        print(json.dumps({"unit": args.unit, "ready": True, "cached": True, "cost": 0}))
        return 0
    outcome = generate(args.repo, args.unit, args.out / "work", args.key.read_text().strip(),
                       record=out.write)
    out.write("report.json", json.dumps(outcome.report, indent=1))
    if outcome.ready:
        out.write("cases.py", outcome.source)
        if cache:
            cache.write(f"{ckey}/cases.py", outcome.source)
            cache.write(f"{ckey}/report.json", json.dumps(outcome.report, indent=1))
    r = outcome.report
    print(json.dumps({"unit": args.unit, "ready": outcome.ready, "kept": len(r["kept"]),
                      "rounds": len(r["rounds"]), "s": r["seconds"],
                      "llm_s": [c.get("seconds") for c in r["calls"]], "cost": r["cost"],
                      "reason": outcome.reason or None,
                      "errors": [c["error"] for c in r["calls"] if c.get("error")]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
