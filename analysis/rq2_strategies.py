"""RQ2: how agents repaired each frequent root cause, from the hand-coded strategies.

Reads:
  analysis/rq2_strategy_coding.csv   the strategy of every edit, named by hand after
                                     reading output/rq2/dossiers/<root cause>.md
  output/rq2/edits.csv               the edits, with verdicts, savings and lines changed
                                     (written by rq2_repair_dossiers.py)

Counting: an instance (one root cause in one unit) counts ONCE per strategy, even
when several runs repaired it the same way. If its repairs used two different
strategies, it counts once under each. For an (instance, strategy) pair:
  confirmed   at least one of its edits with that strategy was confirmed or partial
  saving      the best confirmed saving among those edits
  lines       the lines changed by that best edit

Writes to analysis/output/rq2/:
  strategies.csv               one row per (root cause, strategy)
  strategies_by_root_cause.csv one row per root cause: how many strategies, the main one
  strategies_overall.csv       one row per strategy, over all root causes
  strategies_summary.json      totals

Run after rq2_repair_dossiers.py:  python3 analysis/rq2_strategies.py
"""

import csv

from common import OUTPUT_DIR, ROOT, median, percent, write_csv, write_json

OUT = OUTPUT_DIR / "rq2"   # where this script writes
CODING = ROOT / "analysis" / "rq2_strategy_coding.csv"


def read_coding():
    """{(root cause, edit): strategy} from the hand-made coding file."""
    with open(CODING) as handle:
        lines = [line for line in handle if not line.startswith("#")]   # skip the comments
    coding = {}
    for row in csv.DictReader(lines):
        coding[(row["root_cause"], row["edit"])] = row["strategy"]
    return coding


def pairs_of(coding):
    """{(root cause, instance, strategy): {"confirmed", "saving", "lines"}} from edits.csv."""
    pairs = {}
    with open(OUT / "edits.csv") as handle:
        for edit in csv.DictReader(handle):
            strategy = coding[(edit["root_cause"], edit["edit"])]
            key = (edit["root_cause"], edit["instance"], strategy)
            # Empty when the edit has no confirmed measurement
            saving = float(edit["best_saving_pct"]) if edit["best_saving_pct"] else None
            confirmed = edit["confirmed"] == "True"
            if key not in pairs:
                pairs[key] = {"confirmed": confirmed, "saving": saving,
                              "lines": int(edit["lines_changed"])}
            else:
                pair = pairs[key]
                pair["confirmed"] = pair["confirmed"] or confirmed
                if saving is not None and (pair["saving"] is None or saving > pair["saving"]):
                    pair["saving"] = saving              # keep the best edit of this strategy
                    pair["lines"] = int(edit["lines_changed"])
    return pairs


def describe(pairs):
    """Counts for a group of (instance, strategy) pairs."""
    savings = [p["saving"] for p in pairs if p["confirmed"]]
    return {"instances": len(pairs),
            "confirmed": len([p for p in pairs if p["confirmed"]]),
            "median_saving_confirmed_pct": round(median(savings), 1) if savings else None,
            "median_lines_changed": float(median([p["lines"] for p in pairs]))}   # 5 -> 5.0, like 5.5


def main():
    coding = read_coding()
    pairs = pairs_of(coding)

    # One row per (root cause, strategy), the most used strategy first
    by_cause = {}
    for (cause, instance, strategy), pair in pairs.items():
        by_cause.setdefault(cause, {}).setdefault(strategy, []).append(pair)
    rows = []
    per_cause = []
    for cause in by_cause:
        strategies = by_cause[cause]
        instances = {instance for (c, instance, s) in pairs if c == cause}
        ordered = sorted(strategies, key=lambda s: (-len(strategies[s]), s))
        for strategy in ordered:
            line = {"root_cause": cause, "strategy": strategy}
            line.update(describe(strategies[strategy]))
            rows.append(line)
        main_strategy = ordered[0]
        with_two = 0                                     # instances repaired in 2+ ways
        for instance in instances:
            used = [s for (c, i, s) in pairs if c == cause and i == instance]
            if len(used) > 1:
                with_two = with_two + 1
        everything = [p for (c, i, s), p in pairs.items() if c == cause]
        per_cause.append({
            "root_cause": cause,
            "measured_instances": len(instances),
            "strategies": len(strategies),
            "main_strategy": main_strategy,
            "main_strategy_instances": len(strategies[main_strategy]),
            "pct_instances_main_strategy": percent(len(strategies[main_strategy]), len(instances)),
            "instances_with_2_strategies": with_two,
            "median_lines_changed": float(median([p["lines"] for p in everything])),
        })
    write_csv(rows, OUT / "strategies.csv")
    write_csv(per_cause, OUT / "strategies_by_root_cause.csv")

    # One row per strategy over all root causes: the same move can serve several
    by_strategy = {}
    for (cause, instance, strategy), pair in pairs.items():
        by_strategy.setdefault(strategy, {"causes": set(), "pairs": []})
        by_strategy[strategy]["causes"].add(cause)
        by_strategy[strategy]["pairs"].append(pair)
    overall = []
    for strategy in sorted(by_strategy, key=lambda s: (-len(by_strategy[s]["pairs"]), s)):
        line = {"strategy": strategy,
                "root_causes": " ".join(sorted(by_strategy[strategy]["causes"])),
                "number_of_root_causes": len(by_strategy[strategy]["causes"])}
        line.update(describe(by_strategy[strategy]["pairs"]))
        overall.append(line)
    write_csv(overall, OUT / "strategies_overall.csv")

    summary = {
        "edits_coded": len(coding),
        "instance_strategy_pairs": len(pairs),
        "distinct_strategies": len(by_strategy),
        "strategies_used_for_2_or_more_root_causes": len([s for s in overall if s["number_of_root_causes"] >= 2]),
        "root_causes": len(per_cause),
        "root_causes_with_one_strategy": len([c for c in per_cause if c["strategies"] == 1]),
        "instances_with_2_strategies": sum(c["instances_with_2_strategies"] for c in per_cause),
    }
    write_json(summary, OUT / "strategies_summary.json")
    print("wrote", OUT / "strategies_*")


if __name__ == "__main__":
    main()
