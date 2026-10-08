#!/usr/bin/env python3
"""Compare two measurement runs of the same suite, file by file.

    python validation/compare_runs.py                       # run2 vs run3
    python validation/compare_runs.py run1 run3 --out /tmp

Writes two PNGs next to the results by default:

    compare_energy_time.png   what each run measured, per case file
    compare_verdicts.png      what each run concluded, per case file

The question both plots answer is whether a second run of the same suite says
the same thing as the first. Points on the diagonal agree; distance from it is
how much the answer moved between runs.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")                      # no display on the measurement host
import matplotlib.pyplot as plt

RESULTS = Path(__file__).resolve().parent / "results"

STATUSES = ["confirmed", "mixed", "regressed", "negligible",
            "inconclusive", "timeout", "not_equivalent", "error"]

COLOURS = {
    "confirmed":      "#2a9d5c",
    "mixed":          "#d8a13a",
    "regressed":      "#c2453e",
    "negligible":     "#7d7d7d",
    "inconclusive":   "#5a7fb5",
    "timeout":        "#6b4a8f",
    "not_equivalent": "#8a5a2b",
    "error":          "#000000",
}


def load(tag: str) -> dict[str, dict]:
    """Rows of one run, keyed by case file."""
    path = RESULTS / f"taxonomy.{tag}.jsonl"
    if not path.exists():
        path = RESULTS / f"{tag}.jsonl"
    if not path.exists():
        raise SystemExit(f"no results file for {tag!r} (looked in {RESULTS})")
    rows = {}
    for line in path.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            rows[row["case_file"]] = row
    return rows


def totals(row: dict) -> tuple[float, float]:
    """Energy saved and time saved for a whole case file, as percentages.

    Rows store joules and seconds per case and promote none of them, so a
    file-level figure is the sum across its cases: all the energy `before`
    spent against all the energy `after` spent. Summing weights each case by
    how much it actually costs, which is the point of not nominating one.
    """
    cases = row.get("per_case") or []
    be = sum(c.get("before_energy_j") or 0.0 for c in cases)
    ae = sum(c.get("after_energy_j") or 0.0 for c in cases)
    bt = sum(c.get("before_time_s") or 0.0 for c in cases)
    at = sum(c.get("after_time_s") or 0.0 for c in cases)
    energy = 100.0 * (be - ae) / be if be > 0 else float("nan")
    time = 100.0 * (bt - at) / bt if bt > 0 else float("nan")
    return energy, time


def _diagonal(ax, lo: float, hi: float) -> None:
    """The line where the two runs agree, plus a +-5 point band around it."""
    ax.plot([lo, hi], [lo, hi], color="#444", lw=1, zorder=1)
    ax.fill_between([lo, hi], [lo - 5, hi - 5], [lo + 5, hi + 5],
                    color="#444", alpha=0.08, zorder=0)
    ax.axhline(0, color="#bbb", lw=0.6, zorder=0)
    ax.axvline(0, color="#bbb", lw=0.6, zorder=0)


def plot_measurements(a_tag, b_tag, a_rows, b_rows, shared, out: Path) -> Path:
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.2))

    for ax, index, name in ((axes[0], 0, "Energy"), (axes[1], 1, "Wall-clock time")):
        xs, ys, colours = [], [], []
        for case in shared:
            x = totals(a_rows[case])[index]
            y = totals(b_rows[case])[index]
            if x != x or y != y:                       # NaN: nothing measured
                continue
            xs.append(x)
            ys.append(y)
            colours.append(COLOURS.get(b_rows[case]["status"], "#888"))

        lo = min(xs + ys + [0]) * 1.2 - 5
        hi = max(xs + ys + [0]) * 1.2 + 5
        _diagonal(ax, lo, hi)
        ax.scatter(xs, ys, c=colours, s=26, alpha=0.85, edgecolor="none", zorder=3)
        # A repair that runs 20x slower reads -2000%, and on linear axes a
        # handful of those flatten every ordinary result into one corner.
        # Symlog keeps the -100..100 band where most files live readable while
        # still showing the outliers in place.
        ax.set_xscale("symlog", linthresh=100)
        ax.set_yscale("symlog", linthresh=100)
        ax.set_xlim(lo, hi)
        ax.set_ylim(lo, hi)
        ax.set_aspect("equal")
        ax.grid(alpha=0.15, lw=0.5)
        ax.set_xlabel(f"{a_tag}:  % saved")
        ax.set_ylabel(f"{b_tag}:  % saved")

        moved = [abs(y - x) for x, y in zip(xs, ys)]
        moved.sort()
        median = moved[len(moved) // 2]
        within = 100.0 * sum(1 for m in moved if m <= 5) / len(moved)
        ax.set_title(f"{name}\n{len(xs)} case files   "
                     f"median shift {median:.1f} pts   {within:.0f}% within 5 pts",
                     fontsize=11)

    handles = [plt.Line2D([], [], marker="o", ls="", color=COLOURS[s], label=s)
               for s in STATUSES if any(r["status"] == s for r in b_rows.values())]
    fig.legend(handles=handles, loc="lower center", ncol=len(handles),
               frameon=False, fontsize=9, title=f"verdict in {b_tag}")
    fig.suptitle(f"Does a second run measure the same thing?   "
                 f"{a_tag} vs {b_tag}, per case file", fontsize=13)
    fig.tight_layout(rect=(0, 0.07, 1, 0.96))
    path = out / "compare_energy_time.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def plot_verdicts(a_tag, b_tag, a_rows, b_rows, shared, out: Path) -> Path:
    present = [s for s in STATUSES
               if any(r["status"] == s for r in list(a_rows.values()) + list(b_rows.values()))]
    index = {s: i for i, s in enumerate(present)}

    grid = [[0] * len(present) for _ in present]
    for case in shared:
        grid[index[a_rows[case]["status"]]][index[b_rows[case]["status"]]] += 1

    fig, axes = plt.subplots(1, 2, figsize=(13, 6.2),
                             gridspec_kw={"width_ratios": [1.15, 1]})

    # -- left: where each file's verdict went
    ax = axes[0]
    ax.imshow([[v or float("nan") for v in row] for row in grid],
              cmap="Blues", aspect="auto")
    for i in range(len(present)):
        for j in range(len(present)):
            if grid[i][j]:
                agree = i == j
                ax.text(j, i, grid[i][j], ha="center", va="center",
                        fontsize=11, fontweight="bold" if agree else "normal",
                        color="#1a1a1a")
    ax.set_xticks(range(len(present)), present, rotation=35, ha="right", fontsize=9)
    ax.set_yticks(range(len(present)), present, fontsize=9)
    ax.set_xlabel(f"{b_tag}")
    ax.set_ylabel(f"{a_tag}")
    same = sum(grid[i][i] for i in range(len(present)))
    ax.set_title(f"Verdict in each run\n{same} of {len(shared)} agree "
                 f"({100.0 * same / len(shared):.0f}%)  —  diagonal is agreement",
                 fontsize=11)

    # -- right: totals per run, side by side
    ax = axes[1]
    a_count = Counter(r["status"] for r in a_rows.values())
    b_count = Counter(r["status"] for r in b_rows.values())
    positions = range(len(present))
    width = 0.38
    ax.bar([p - width / 2 for p in positions], [a_count[s] for s in present],
           width, label=a_tag, color="#7d9fc4", edgecolor="none")
    ax.bar([p + width / 2 for p in positions], [b_count[s] for s in present],
           width, label=b_tag, color="#c47d7d", edgecolor="none")
    for p in positions:
        for offset, count in ((-width / 2, a_count[present[p]]),
                              (width / 2, b_count[present[p]])):
            if count:
                ax.text(p + offset, count + 1, count, ha="center", fontsize=9)
    ax.set_xticks(list(positions), present, rotation=35, ha="right", fontsize=9)
    ax.set_ylabel("case files")
    ax.legend(frameon=False)
    ax.set_title("How many of each verdict", fontsize=11)
    ax.spines[["top", "right"]].set_visible(False)

    fig.suptitle(f"Does a second run reach the same conclusion?   "
                 f"{a_tag} vs {b_tag}", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    path = out / "compare_verdicts.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("first", nargs="?", default="run2")
    parser.add_argument("second", nargs="?", default="run3")
    parser.add_argument("--out", type=Path, default=RESULTS)
    args = parser.parse_args()

    a_rows = load(args.first)
    b_rows = load(args.second)
    shared = sorted(set(a_rows) & set(b_rows))
    # Two runs that share a seed differ only where they were actually
    # re-measured; comparing the seeded rows would compare a file with itself
    # and bury the handful of rows the comparison is about.
    moved = [c for c in shared
             if json.dumps(a_rows[c].get("per_case")) != json.dumps(b_rows[c].get("per_case"))]
    if moved and len(moved) < len(shared) // 2:
        print(f"note: {len(shared) - len(moved)} rows are identical in both "
              f"(a shared seed); comparing the {len(moved)} that were re-measured")
        shared = moved
    if not shared:
        raise SystemExit("the two runs have no case files in common")

    only_a = len(a_rows) - len(shared)
    only_b = len(b_rows) - len(shared)
    print(f"{args.first}: {len(a_rows)} rows   {args.second}: {len(b_rows)} rows   "
          f"compared: {len(shared)}"
          + (f"   (skipped {only_a} + {only_b} not in both)" if only_a or only_b else ""))

    args.out.mkdir(parents=True, exist_ok=True)
    for path in (plot_measurements(args.first, args.second, a_rows, b_rows, shared, args.out),
                 plot_verdicts(args.first, args.second, a_rows, b_rows, shared, args.out)):
        print("wrote", path)

    # The numbers behind the plots, for anyone reading this in a terminal.
    moved = sorted(
        (abs(totals(b_rows[c])[0] - totals(a_rows[c])[0]), c)
        for c in shared
        if totals(a_rows[c])[0] == totals(a_rows[c])[0]
        and totals(b_rows[c])[0] == totals(b_rows[c])[0]
    )
    median = moved[len(moved) // 2][0]
    print(f"\nenergy shift between runs: median {median:.1f} points, "
          f"{100.0 * sum(1 for m, _ in moved if m <= 5) / len(moved):.0f}% within 5 points")
    print("largest disagreements:")
    for shift, case in moved[-5:][::-1]:
        print(f"  {shift:6.1f} pts  {a_rows[case]['status']:<12} -> "
              f"{b_rows[case]['status']:<12} {case.split('/')[-1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
