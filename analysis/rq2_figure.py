"""RQ2 figure: for each frequent root cause, how much it saves and how reliably.

Reads output/rq2/root_causes_table.csv (written by rq2_root_causes.py): the root
causes with at least 3 measured instances. Each root cause is one point:
  x     the median best saving of its confirmed instances, in percent
  y     the share of its measured instances that are confirmed, in percent
  size  how many of its instances were measured
Two dashed lines mark the same two numbers over all instances (the "All" row of
output/rq2/categories.csv), so each root cause can be read against the whole.

One ink, no color: the figure reads the same in grayscale.

Writes output/rq2/fig_rq2_root_causes.pdf and .png, and copies the PDF to
temp_main_paper/results/generated/.

Run after rq2_root_causes.py:  python3 analysis/rq2_figure.py
"""

import csv
import shutil

import matplotlib
matplotlib.use("Agg")                      # draw to files, no window
import matplotlib.pyplot as plt            # noqa: E402

from common import OUTPUT_DIR, ROOT        # noqa: E402

RQ2 = OUTPUT_DIR / "rq2"
PAPER = ROOT / "temp_main_paper" / "results" / "generated"
INK = "#333333"                            # one dark ink for every mark and text
SIZE_PER_INSTANCE = 7                      # marker area per measured instance

# Where each label sits relative to its point, in points (x, y), so that labels
# do not cover each other. Only the placement is set by hand; no value is.
LABEL_OFFSET = {
    "C1.S4": (5, -9), "C3.S2": (7, -3), "C8.S2": (5, 2),
    "C6.S2": (-12, -14), "C9.S1": (-27, -2), "C6.S3": (5, 2), "C10.S2": (-6, -10),
    "C1.S1": (-24, 3), "C10.S1": (5, -8), "C3.S5": (-14, 4), "C8.S3": (-4, 7),
    "C10.S3": (-9, -12), "C10.S4": (5, 2), "C3.S1": (5, -3), "C3.S4": (-8, -11),
    "C4.S7": (5, 2), "C7.S1": (-10, 4),
}


def read_rows(path):
    with open(path) as handle:
        return list(csv.DictReader(handle))


def main():
    causes = read_rows(RQ2 / "root_causes_table.csv")
    everything = [r for r in read_rows(RQ2 / "categories.csv") if r["category"] == "All"][0]

    # Font sizes chosen for a figure printed one column wide (about 3.5 inches)
    plt.rcParams.update({"font.family": "STIXGeneral", "mathtext.fontset": "stix",
                         "font.size": 8, "axes.labelsize": 8, "xtick.labelsize": 7,
                         "ytick.labelsize": 7, "legend.fontsize": 7})
    fig, ax = plt.subplots(figsize=(3.5, 2.6))

    # The two reference lines: all instances together
    ax.axvline(float(everything["median_best_saving_pct"]), color="#999999", linewidth=0.7,
               linestyle=(0, (3, 2)), zorder=1)
    ax.axhline(float(everything["pct_measured_confirmed"]), color="#999999", linewidth=0.7,
               linestyle=(0, (3, 2)), zorder=1)

    for row in causes:                                  # one point per root cause
        x = float(row["median_best_saving_pct"])
        y = float(row["pct_measured_confirmed"])
        size = SIZE_PER_INSTANCE * int(row["measured"])
        ax.scatter([x], [y], s=size, facecolors="white", edgecolors=INK, linewidths=0.8, zorder=3)
        ax.annotate(row["root_cause"], (x, y), xytext=LABEL_OFFSET.get(row["root_cause"], (5, 2)),
                    textcoords="offset points", fontsize=6.5, color=INK, zorder=4)

    # A legend for the marker size: three example sizes
    for n in (3, 8, 13):
        ax.scatter([], [], s=SIZE_PER_INSTANCE * n, facecolors="white", edgecolors=INK,
                   linewidths=0.8, label=f"{n}")
    ax.legend(title="Measured instances", title_fontsize=7, loc="lower right", frameon=False,
              ncol=3, handletextpad=0.1, columnspacing=0.8, borderaxespad=0.2)

    ax.set_xlabel("Median best saving of confirmed instances (%)")
    ax.set_ylabel("Measured instances confirmed (%)")
    ax.set_xlim(0, 80)
    ax.set_ylim(15, 110)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.grid(color="#eeeeee", linewidth=0.5, zorder=0)   # a quiet grid
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.tick_params(length=2, color=INK, labelcolor=INK)
    fig.tight_layout(pad=0.3)
    fig.savefig(RQ2 / "fig_rq2_root_causes.pdf")
    fig.savefig(RQ2 / "fig_rq2_root_causes.png", dpi=300)
    PAPER.mkdir(parents=True, exist_ok=True)
    shutil.copy(RQ2 / "fig_rq2_root_causes.pdf", PAPER / "fig_rq2_root_causes.pdf")
    print("wrote", RQ2 / "fig_rq2_root_causes.pdf", "and .png")


if __name__ == "__main__":
    main()
