"""RQ1 figure: the energy saving of every repair that saves energy.

Reads output/rq1/step3_all_savings.csv (written by rq1_step3.py): one row per
repair whose verdict is confirmed or partial, with its saving in percent.

Draws one panel per repository. In each panel, the x-axis has the three skills,
and every repair is one point at its saving. Sonnet's repairs are filled circles
on the left of each skill, Haiku's are open triangles on the right; a short
horizontal bar marks the median of each group. Points are spread sideways by a
small random amount so they do not hide each other. The random numbers come
from a fixed seed, so the figure is the same every time.

The models are told apart by marker shape and fill, not by color, so the figure
reads the same in grayscale and for color-blind readers.

Writes output/rq1/fig_rq1_savings.pdf and .png, and copies the PDF to
temp_main_paper/results/generated/.

Run after rq1_step3.py:  python3 analysis/rq1_figure.py
"""

import csv
import random
import shutil

import matplotlib
matplotlib.use("Agg")                      # draw to files, no window
import matplotlib.pyplot as plt            # noqa: E402

from common import OUTPUT_DIR, REPOS, ROOT, median   # noqa: E402

RQ1 = OUTPUT_DIR / "rq1"
PAPER = ROOT / "temp_main_paper" / "results" / "generated"
SEED = 7                                   # fixed seed for the sideways spread
SKILL_ORDER = ["Taxonomy+Rules", "Taxonomy", "Unguided"]
INK = "#333333"                            # one dark ink for every mark and text

# Sonnet: filled circle, left of the skill's position. Haiku: open triangle, right.
STYLE = {
    "Sonnet": {"marker": "o", "facecolor": INK, "offset": -0.17},
    "Haiku": {"marker": "^", "facecolor": "none", "offset": +0.17},
}


def read_savings():
    """{(repo, skill, model): [savings]} from step3_all_savings.csv."""
    savings = {}
    with open(RQ1 / "step3_all_savings.csv") as handle:
        for row in csv.DictReader(handle):
            key = (row["repo"], row["skill"], row["model"])
            if key not in savings:
                savings[key] = []
            savings[key].append(float(row["saving_pct"]))
    return savings


def main():
    savings = read_savings()
    spread = random.Random(SEED)           # the fixed random source for the jitter

    # Font sizes chosen for a figure printed one column wide (about 3.5 inches)
    plt.rcParams.update({"font.family": "STIXGeneral", "mathtext.fontset": "stix",
                         "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 8,
                         "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 7})

    fig, axes = plt.subplots(1, 3, figsize=(3.5, 2.2), sharey=True)
    for panel, repo in enumerate(REPOS):
        ax = axes[panel]
        for x, skill in enumerate(SKILL_ORDER):            # x = 0, 1, 2 for the three skills
            for model, style in STYLE.items():
                values = savings.get((repo, skill, model), [])
                centre = x + style["offset"]               # where this group sits on the x-axis
                xs = []
                for _ in values:                           # a small sideways shift per point
                    xs.append(centre + spread.uniform(-0.09, 0.09))
                ax.scatter(xs, values, s=9, marker=style["marker"], linewidths=0.6,
                           facecolors=style["facecolor"], edgecolors=INK, zorder=3,
                           label=model if (panel == 0 and x == 0) else None)
                if values:                                 # the median of the group
                    m = median(values)
                    ax.plot([centre - 0.13, centre + 0.13], [m, m], color=INK, linewidth=1.2, zorder=4)
        ax.set_title(repo, pad=3)
        ax.set_xticks([0, 1, 2])
        ax.set_xticklabels(["Tax.+\nRules", "Tax.", "Ung."])
        ax.set_xlim(-0.55, 2.55)
        ax.set_ylim(0, 105)
        ax.grid(axis="y", color="#dddddd", linewidth=0.5, zorder=0)   # a quiet grid
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        ax.tick_params(length=2, color=INK, labelcolor=INK)

    axes[0].set_ylabel("Energy saving (%)")
    # The legend goes in one row above the panels, where it covers no point
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False,
               handletextpad=0.2, columnspacing=1.2, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(pad=0.3, w_pad=0.4, rect=(0, 0, 1, 0.93))   # leave the top 7% for the legend
    fig.savefig(RQ1 / "fig_rq1_savings.pdf")
    fig.savefig(RQ1 / "fig_rq1_savings.png", dpi=300)
    PAPER.mkdir(parents=True, exist_ok=True)
    shutil.copy(RQ1 / "fig_rq1_savings.pdf", PAPER / "fig_rq1_savings.pdf")
    print("wrote", RQ1 / "fig_rq1_savings.pdf", "and .png")


if __name__ == "__main__":
    main()
