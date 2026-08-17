"""Build-time tooling: turns the taxonomy and catalog into the shipped skill.

Nothing here is part of the deliverable. `python -m build` reads
`taxonomy/*.xlsx` and `catalog/*.yaml` and writes `skill/reference/*.md` plus
`skill/scripts/lib/signals.json`.

Requires `pandas`, `openpyxl` and `pyyaml`. The skill itself requires none of
them -- that asymmetry is the point of having a build step at all.
"""
