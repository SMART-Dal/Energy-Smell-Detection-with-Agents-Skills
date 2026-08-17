#!/usr/bin/env python3
"""Write one verifier case file per sample pair in data/manual_sampling.

    python validation/generate_sample_cases.py

Each generated file is three lines, because all the work is in `_sample.build`.
They exist as files rather than as one loop so that any single pair can be
re-run, edited or argued with on its own:

    python skill/scripts/verify.py validation/samples/BuiltInBehavior__SumTopK.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "validation" / "samples"
SAMPLES = ROOT / "data" / "manual_sampling"

TEMPLATE = '''"""Generated from data/manual_sampling/{category}/{name}.

Do not edit: regenerate with `python validation/generate_sample_cases.py`.
The pair itself is the thing under test, so the case file must stay a faithful
transcription of it.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _sample import build  # noqa: E402
{relaxation}
before, after, cases = build({category!r}, {name!r})
'''

RETURNS_ONLY = {
    "BuiltInBehavior/SumTopK":
        "`lst.sort()` sorts the caller's list in place where `sorted(lst)` "
        "returns a new one. Both return the same sum.",
    "OveruseOfLoops/MergeLists":
        "`lst1.extend(lst2)` grows the caller's list where `lst1 + lst2` "
        "allocates a new one. Both return the same sequence.",
    "BuiltInBehavior/OperatingOnList2":
        "the repair rewrites the input in place instead of building a new "
        "list. Both return the same values.",
}
"""Pairs whose two sides compute the same answer but differ in what they mutate.

The project owner's position, and it is the right one: what a function is *for*
is the answer it produces, and a refactoring that stops disturbing the caller's
data has not changed the functionality. Whether that is safe depends on the call
sites, which is a judgement about a particular program rather than about the
pair -- so it is declared per pair, with the reason, and the verdict repeats it.

This is not a general relaxation. Pairs that return a *different answer* --
indices where the original returned values, a set where it returned a list, an
off-by-one -- stay rejected, because there the two sides do different things.
"""


def main() -> int:
    sys.path.insert(0, str(OUT))
    from _sample import SampleError, build  # noqa: PLC0415

    OUT.mkdir(parents=True, exist_ok=True)
    written, skipped = 0, []

    for directory in sorted(p for p in SAMPLES.glob("*/*") if p.is_dir()):
        category, name = directory.parent.name, directory.name
        try:
            build(category, name)
        except Exception as exc:  # noqa: BLE001 -- report, do not abort the batch
            skipped.append((f"{category}/{name}", str(exc).split("\n")[0][:90]))
            continue
        reason = RETURNS_ONLY.get(f"{category}/{name}")
        relaxation = (
            f'\n# Same answer, different side effect: {reason}\n'
            f'EQUIVALENCE = "returns_only"\n'
            if reason else ""
        )
        (OUT / f"{category}__{name}.py").write_text(
            TEMPLATE.format(category=category, name=name, relaxation=relaxation)
        )
        written += 1

    print(f"wrote {written} case files to {OUT.relative_to(ROOT)}")
    if skipped:
        print(f"\n{len(skipped)} pairs need converting by hand:")
        for pair, reason in skipped:
            print(f"  {pair:50} {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
