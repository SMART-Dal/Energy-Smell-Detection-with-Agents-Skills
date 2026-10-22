#!/usr/bin/env python3
"""Install a repository's dependencies into the current venv, in one resolve.

    repo_deps.py REPO_DIR [BASE ...]

BASE is passed to pip as given (our own tools: `-r requirements.txt numpy ...`).
On top of it go every requirements*.txt within three levels of the root, and
what every setup.py or pyproject.toml there declares, all in ONE pip call, so
pip chooses versions that work together. Installing them one call at a time
let a later call upgrade what an earlier pin depended on: urllib3 2.x under a
2022 botocore, and `import boto3` failed for the whole repository.

If the repository's own pins cannot be satisfied together, they are dropped
(names kept) and the resolve is tried again; only if that fails too does each
requirement go in on its own. Either way the dropped pins are then put back one
at a time wherever one fits without moving anything else (`restore_pins`).
`pip check` runs at the end, and every fallback and problem is printed as a
WARNING line.

The repository's own code is never installed: an installed copy would shadow
the copies verify.py measures. So `-e`, local paths and the projects
themselves are left out, and a project's declared dependencies are read from a
throwaway copy of the whole repository -- building its metadata in place would
leave an egg-info in the pristine clone, and a copy of the project folder alone
breaks a setup.py that reaches into its parents (`../../LICENSE`, `../../lib`).
"""

from __future__ import annotations

import json
import re
import shutil
import ast
import subprocess
import sys
import tempfile
from pathlib import Path

SKIP = {".git", "node_modules", "venv", ".venv", "site-packages", "docs", "examples"}
NAME = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)(\[[^\]]*\])?")


def files(root: Path, pattern: str) -> list[Path]:
    found = []
    for path in sorted(root.rglob(pattern)):
        rel = path.relative_to(root)
        if len(rel.parts) <= 4 and not SKIP & set(rel.parts):
            found.append(path)
    return found


def pip(*args: str, quiet_fail: bool = False) -> bool:
    try:
        done = subprocess.run([sys.executable, "-m", "pip", *args], capture_output=True,
                              text=True, timeout=1800)
    except subprocess.TimeoutExpired:
        print("  timed out")
        return False
    if done.returncode != 0 and not quiet_fail:
        lines = [l for l in done.stderr.strip().splitlines() if l.strip()] or ["?"]
        print("  failed:", " | ".join(lines[-3:])[:400])
    return done.returncode == 0


def requirement_lines(path: Path, seen: set[Path]) -> list[str]:
    """The installable third-party requirements of one file, includes followed."""
    path = path.resolve()
    if path in seen or not path.is_file():
        return []
    seen.add(path)
    out = []
    for raw in path.read_text(errors="replace").splitlines():
        line = re.sub(r"(^|\s)#.*$", "", raw).strip()
        line = re.sub(r"\s--hash[= ]\S+", "", line).strip()
        if not line:
            continue
        include = re.match(r"^(-r|--requirement)[=\s]+(\S+)", line)
        if include:
            out += requirement_lines(path.parent / include.group(2), seen)
            continue
        if line.startswith(("-", ".", "/", "file:")) or ("://" in line and " @ " not in line):
            continue                    # options, editables, local paths: the repo's own code
        out.append(line)
    return out


def declared(project: Path) -> list[str] | None:
    """What a setup.py / pyproject.toml project depends on. `project` is inside a
    throwaway copy of the repository, never the pristine clone."""
    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "report.json"
        if not pip("install", "-q", "--dry-run", "--no-deps", "--ignore-installed",
                   "--report", str(report), str(project)):
            return None
        items = json.loads(report.read_text()).get("install", [])
    requested = [i for i in items if i.get("requested")]
    if not requested:
        return []
    return [r for r in requested[0]["metadata"].get("requires_dist") or []
            if "extra ==" not in r.replace('"', "").replace("'", "")]


def canonical(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def restore_pins(specs: list[str]) -> None:
    """Put back each version the relaxed install dropped, where it still fits.

    When any two of a repository's pins conflict, every pin is dropped. In
    sample-apps (Oct 22) that installed colpali-engine 0.2.2 under code written
    for the pinned 0.3.18, and two of its units could not load. So each
    requirement the installed version does not satisfy is tried on its own,
    with every other package held at its installed version: pip either installs
    it without moving anything else, or changes nothing. The first pin of a
    package that fits wins; a later, different pin of the same package is
    reported, not applied over it.
    """
    try:
        from packaging.requirements import InvalidRequirement, Requirement
    except ImportError:
        from pip._vendor.packaging.requirements import InvalidRequirement, Requirement
    from importlib import metadata

    restored, conflicting, unrestorable = {}, [], []
    for spec in specs:
        try:
            req = Requirement(spec)
        except InvalidRequirement:
            continue
        if not req.specifier or req.url or (req.marker and not req.marker.evaluate()):
            continue
        try:
            installed = metadata.version(req.name)
        except metadata.PackageNotFoundError:
            continue
        if req.specifier.contains(installed, prereleases=True):
            continue
        name = canonical(req.name)
        if name in restored:
            conflicting.append(f"{spec} (kept {req.name}=={installed}, from {restored[name]})")
            continue
        freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True,
                                text=True).stdout
        held = [line for line in freeze.splitlines() if "==" in line and not line.startswith("-e")
                and canonical(line.split("==", 1)[0]) != name]
        with tempfile.TemporaryDirectory() as tmp:
            pins = Path(tmp) / "held.txt"
            pins.write_text("\n".join(held) + "\n")
            if pip("install", "-q", "-c", str(pins), spec, quiet_fail=True):
                restored[name] = spec
                print(f"pin restored: {spec} (was {installed})")
            else:
                unrestorable.append(f"{spec} (installed {installed})")
    for line in unrestorable:
        print(f"WARNING: pin not restored, it would move other packages: {line}")
    for line in conflicting:
        print(f"WARNING: pin not restored, another pin of the package was: {line}")


def relaxed(spec: str) -> str:
    """`boto3==1.22.8; python_version>'3'` -> `boto3; python_version>'3'`."""
    match = NAME.match(spec)
    if not match:
        return spec
    marker = spec.split(";", 1)[1].strip() if ";" in spec else ""
    return match.group(1) + (match.group(2) or "") + (f"; {marker}" if marker else "")


# Libraries a repository's code imports without declaring them anywhere: bsdd's
# converter calls tqdm, which no requirements file names, so verify.py could only
# stub it and refused to measure. Only these well-known names are installed --
# installing whatever PyPI package happens to share an import's name would pull
# in strangers (`handler`, `commons`) or name-squatters -- and never the heavy
# optional stacks (torch, langchain, onnx), which a developer installs on purpose.
WELL_KNOWN = {
    "aiohttp": "aiohttp", "attr": "attrs", "boto3": "boto3", "botocore": "botocore",
    "bs4": "beautifulsoup4", "click": "click", "colorama": "colorama",
    "cryptography": "cryptography", "dateutil": "python-dateutil", "docker": "docker",
    "faker": "Faker", "fire": "fire", "flask": "flask", "html5lib": "html5lib",
    "httpx": "httpx", "jinja2": "Jinja2",
    "jsonschema": "jsonschema", "lxml": "lxml", "markdownify": "markdownify",
    "matplotlib": "matplotlib", "mmh3": "mmh3", "mock": "mock", "msal": "msal",
    "nest_asyncio": "nest_asyncio", "numpy": "numpy", "openpyxl": "openpyxl",
    "packaging": "packaging", "pandas": "pandas", "PIL": "pillow",
    "pkg_resources": "setuptools", "psutil": "psutil", "pyarrow": "pyarrow",
    "pytest": "pytest", "pytz": "pytz", "regex": "regex", "requests": "requests",
    "scipy": "scipy", "simplejson": "simplejson", "six": "six", "sklearn": "scikit-learn",
    "tabulate": "tabulate", "toml": "toml", "tqdm": "tqdm", "ujson": "ujson",
    "xlrd": "xlrd", "yaml": "pyyaml",
}

# Parsers and engines a library loads by name, not by import: sample-apps'
# feed-split.py calls BeautifulSoup(html, 'html5lib'), which needs html5lib
# although no import says so. A call given one of these names as an argument
# counts as an import of it.
NAMED_BY_STRING = {"html5lib", "lxml", "openpyxl", "xlrd", "pyarrow"}


def wanted_imports(tree) -> set[str]:
    """Top-level names a module imports, and the parsers it names in calls."""
    wanted = set()
    for node in ast.walk(tree):
        names = [a.name for a in node.names] if isinstance(node, ast.Import) else \
            [node.module] if isinstance(node, ast.ImportFrom) and not node.level \
            and node.module else []
        wanted |= {n.split(".")[0] for n in names}
        if isinstance(node, ast.Call):
            wanted |= {a.value for a in [*node.args, *(k.value for k in node.keywords)]
                       if isinstance(a, ast.Constant) and a.value in NAMED_BY_STRING}
    return wanted


def undeclared(root: Path) -> None:
    """Install the WELL_KNOWN libraries the code imports but the venv lacks,
    pinned against everything already installed so no version changes."""
    import importlib.util
    local = {p.stem if p.suffix == ".py" else p.name for p in root.rglob("*")
             if ".git" not in p.parts and (p.suffix == ".py" or p.is_dir())}
    wanted = set()
    for file in root.rglob("*.py"):
        if ".git" in file.relative_to(root).parts:
            continue
        try:
            tree = ast.parse(file.read_bytes())
        except (SyntaxError, ValueError):
            continue
        wanted |= wanted_imports(tree)
    missing = sorted(n for n in wanted - local if n in WELL_KNOWN
                     and importlib.util.find_spec(n) is None)
    if not missing:
        return
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True,
                            text=True).stdout
    with tempfile.TemporaryDirectory() as tmp:
        pins = Path(tmp) / "pins.txt"
        pins.write_text("\n".join(l for l in freeze.splitlines()
                                  if "==" in l and not l.startswith("-e")) + "\n")
        packages = [WELL_KNOWN[n] for n in missing]
        print(f"undeclared: the code imports {', '.join(missing)}; installing, pinned")
        if not pip("install", "-q", "-c", str(pins), *packages):
            for package in packages:
                if not pip("install", "-q", "-c", str(pins), package, quiet_fail=True):
                    print(f"WARNING: undeclared import not installed: {package}")


def main() -> int:
    root = Path(sys.argv[1])
    base = sys.argv[2:]

    specs: list[str] = []
    for req in files(root, "requirements*.txt"):
        found = requirement_lines(req, set())
        print(f"requirements: {req.relative_to(root)} ({len(found)})")
        specs += found
    projects = {p.parent for name in ("setup.py", "pyproject.toml") for p in files(root, name)}
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / root.name
        if projects:
            # `.git` comes along (the clones are shallow, so it is small): some
            # setup.py files run git -- rhino's runs `git clean -dfx` -- and
            # here that touches only the copy.
            shutil.copytree(root, copy, symlinks=True, ignore=shutil.ignore_patterns(
                "node_modules", "*.egg-info", "venv", ".venv"))
        for project in sorted(projects):
            relative = project.relative_to(root)
            deps = declared(copy / relative)
            if deps is None:
                print(f"WARNING: project {relative}: could not read its dependencies "
                      f"(above); left out")
                continue
            print(f"project: {relative} ({len(deps)})")
            specs += deps
    specs = list(dict.fromkeys(specs))

    with tempfile.TemporaryDirectory() as tmp:
        as_written = Path(tmp) / "as_written.txt"
        as_written.write_text("\n".join(specs) + "\n")
        loose = list(dict.fromkeys(relaxed(s) for s in specs))
        names_only = Path(tmp) / "names_only.txt"
        names_only.write_text("\n".join(loose) + "\n")

        print(f"install: {len(specs)} repository requirements and our base, one resolve")
        if pip("install", "-q", *base, "-r", str(as_written)):
            print("install: done, as written")
        elif pip("install", "-q", *base, "-r", str(names_only)):
            print("WARNING: the repository's pins conflict; installed with its versions "
                  "dropped (names kept), then restored one by one where they fit")
            restore_pins(specs)
        else:
            print("WARNING: no single resolve works; installing one requirement at a time")
            pip("install", "-q", *base)
            for spec in loose:
                if not pip("install", "-q", spec, quiet_fail=True):
                    print(f"WARNING: not installed: {spec}")
            restore_pins(specs)

    undeclared(root)

    check = subprocess.run([sys.executable, "-m", "pip", "check"], capture_output=True, text=True)
    if check.returncode == 0:
        print("pip check: ok")
    else:
        for line in check.stdout.strip().splitlines():
            print(f"WARNING: pip check: {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
