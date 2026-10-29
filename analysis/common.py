"""Small helpers that every analysis script uses.

Nothing here computes a result. It only says where the files are, which runs
exist, and how to read and write them, so that each RQ script can stay short.
"""

import csv   # to write tables as .csv files
import json  # to read the .json and .jsonl files of each run
import sys   # to make the repo_stats module importable
from pathlib import Path  # to build file paths that work on any system

# ---------------------------------------------------------------------------
# Where things are
# ---------------------------------------------------------------------------

# The project's root folder: this file is in <root>/analysis/common.py
ROOT = Path(__file__).resolve().parent.parent

# The copied runs: results/<repo>/<skill>/<model>/
RESULTS_DIR = ROOT / "results"

# Every file a script writes goes under analysis/output/
OUTPUT_DIR = ROOT / "analysis" / "output"

# The repository sizes, written by experiment/lib/repo_stats.py (see README.md)
REPO_STATS_FILE = OUTPUT_DIR / "repo_stats.tsv"

# ---------------------------------------------------------------------------
# The 18 main runs: 3 repositories x 3 skills x 2 models
# ---------------------------------------------------------------------------

# The repositories, in the order the paper lists them
REPOS = ["sample-apps", "dx-toolkit", "community"]

# The skills (called "arms" in the run folders), most guidance first
SKILLS = ["full", "knowledge", "control"]

# The names the paper uses for the skills
SKILL_NAMES = {
    "full": "Taxonomy+Rules",
    "knowledge": "Taxonomy",
    "control": "Unguided",
}

# The models, the larger one first
MODELS = ["sonnet", "haiku"]

# The model names the paper uses
MODEL_NAMES = {
    "sonnet": "Sonnet",
    "haiku": "Haiku",
}

# ---------------------------------------------------------------------------
# Verdicts of our review (review/results.jsonl, field "status")
# ---------------------------------------------------------------------------

# A repair that saves energy. "partial" counts as a saving: it saves beyond
# its confidence interval on some inputs and costs more on none.
SAVES = {"confirmed", "partial"}

# Every verdict that comes from an actual measurement
MEASURED = {"confirmed", "partial", "mixed", "regressed", "negligible"}


# ---------------------------------------------------------------------------
# Reading files
# ---------------------------------------------------------------------------

def read_json(path):
    """Read one .json file and return what it holds."""
    with open(path) as handle:          # open the file for reading
        return json.load(handle)        # parse the whole file as JSON


def read_jsonl(path):
    """Read a .jsonl file (one JSON object per line) into a list."""
    rows = []                           # the objects read so far
    with open(path) as handle:          # open the file for reading
        for line in handle:             # go through it line by line
            line = line.strip()         # drop the newline and spaces
            if line:                    # skip empty lines
                rows.append(json.loads(line))  # parse the line and keep it
    return rows


def run_folder(repo, skill, model):
    """The folder of one run, e.g. results/dx-toolkit/full/sonnet."""
    return RESULTS_DIR / repo / skill / model


def all_runs():
    """Every (repo, skill, model) of the 18 main runs, in a fixed order."""
    runs = []                           # the list we fill
    for repo in REPOS:                  # each repository
        for skill in SKILLS:            # each skill
            for model in MODELS:        # each model
                runs.append((repo, skill, model))
    return runs


def run_label(repo, skill, model):
    """A readable name for one run, e.g. 'dx-toolkit / Taxonomy / Haiku'."""
    return f"{repo} / {SKILL_NAMES[skill]} / {MODEL_NAMES[model]}"


# ---------------------------------------------------------------------------
# Small facts about units and root causes
# ---------------------------------------------------------------------------

def file_of(unit):
    """The file part of a unit name 'path/to/file.py::Class.method'."""
    return unit.split("::")[0]          # everything before '::'


def category_of(root_cause):
    """The category of a root cause: 'C10.S4' -> 'C10'."""
    return root_cause.split(".")[0]     # everything before the first '.'


# The definition of a test file lives in experiment/lib/repo_stats.py, so the
# repository table and these scripts can never disagree on it.
sys.path.insert(0, str(ROOT / "experiment" / "lib"))
from repo_stats import is_test  # noqa: E402  (imported after the path is set)


def repo_sizes():
    """Units per repository, read from analysis/output/repo_stats.tsv.

    Returns {repo: {"units": ..., "test_units": ..., "files": ...}}.
    """
    sizes = {}                                          # the result
    with open(REPO_STATS_FILE) as handle:               # the file repo_stats.py wrote
        for row in csv.DictReader(handle, delimiter="\t"):   # one row per repository
            name = row["repo"].split("/")[1]            # 'dnanexus/dx-toolkit' -> 'dx-toolkit'
            sizes[name] = {
                "units": int(row["units"]),             # all functions and methods
                "test_units": int(row["test_units"]),   # those in test files
                "files": int(row["files"]),             # Python files
            }
    return sizes


# ---------------------------------------------------------------------------
# Writing files
# ---------------------------------------------------------------------------

def write_csv(rows, path):
    """Write a list of dicts as a .csv table; the keys of the first row are the columns."""
    path.parent.mkdir(parents=True, exist_ok=True)      # make the folder if it is missing
    with open(path, "w", newline="") as handle:         # open the file for writing
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))  # columns
        writer.writeheader()                            # the first line: column names
        writer.writerows(rows)                          # one line per row


def write_json(data, path):
    """Write any data as an indented .json file."""
    path.parent.mkdir(parents=True, exist_ok=True)      # make the folder if it is missing
    with open(path, "w") as handle:                     # open the file for writing
        json.dump(data, handle, indent=2)               # readable, two-space indent


def percent(part, whole):
    """part / whole as a percentage with one decimal, or None when whole is 0."""
    if whole == 0:                      # nothing to divide by
        return None
    return round(100 * part / whole, 1) # e.g. 12 of 40 -> 30.0


def median(values):
    """The middle value of a list (the mean of the two middle ones if even)."""
    ordered = sorted(values)            # smallest to largest
    n = len(ordered)                    # how many values
    if n == 0:                          # an empty list has no median
        return None
    middle = n // 2                     # index of the middle
    if n % 2 == 1:                      # odd count: one middle value
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2   # even: mean of the two middle values


def quartiles(values):
    """The 25th and 75th percentiles, by the same middle-value rule as median()."""
    ordered = sorted(values)            # smallest to largest
    n = len(ordered)                    # how many values
    if n < 2:                           # too few values for quartiles
        return None, None
    lower = ordered[: n // 2]           # the lower half
    upper = ordered[(n + 1) // 2:]      # the upper half (skips the middle value when n is odd)
    return median(lower), median(upper)
