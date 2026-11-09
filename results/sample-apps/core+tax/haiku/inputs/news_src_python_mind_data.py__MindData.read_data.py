# Inputs for news/src/python/mind_data.py::MindData.read_data, generated outside the session: the 4 that used
# the most energy of 8 candidates that ran and repeated on the original.

import copy
import random
from mind_data import MindData

# ---------------------------------------------------------------------------
# Module-level setup: create all files and a master MindData instance.
# Everything here happens before any timing starts.
# ---------------------------------------------------------------------------

_train_news = WORKDIR / "train_news.txt"
_valid_news = WORKDIR / "valid_news.txt"
_train_imp = WORKDIR / "train_impressions.txt"
_valid_imp = WORKDIR / "valid_impressions.txt"

# Minimal news files (empty) so that MindData.__init__ succeeds.
_train_news.write_text("")
_valid_news.write_text("")


def _write_impressions(path, n_lines, imp_mean, hist_mean, n_users, n_news, seed):
    """Write a tab-separated impressions file in the MIND format."""
    rng = random.Random(seed)
    with open(path, "w", encoding="utf-8") as f:
        for i in range(n_lines):
            user = f"U{rng.randrange(n_users)}"

            month = rng.randint(1, 12)
            day = rng.randint(1, 28)
            year = rng.choice([2019, 2020])
            hour = rng.randint(1, 12)
            minute = rng.randint(0, 59)
            second = rng.randint(0, 59)
            ampm = rng.choice(["AM", "PM"])
            time_str = (
                f"{month:02d}/{day:02d}/{year} "
                f"{hour:02d}:{minute:02d}:{second:02d} {ampm}"
            )

            hist_size = max(0, int(rng.gauss(hist_mean, max(1, hist_mean / 2))))
            hist = [f"N{rng.randrange(n_news)}" for _ in range(hist_size)]

            imp_size = max(1, int(rng.gauss(imp_mean, max(1, imp_mean / 2))))
            imps = []
            for _ in range(imp_size):
                news = f"N{rng.randrange(n_news)}"
                label = rng.randint(0, 1)
                imps.append(f"{news}-{label}")

            line = (
                f"{i}\t{user}\t{time_str}\t"
                f"{' '.join(hist)}\t{' '.join(imps)}\n"
            )
            f.write(line)


# Small impressions files used only to build the master instance through
# the repository's own constructor.
_write_impressions(_train_imp, 5, 2, 2, 20, 50, 0)
_write_impressions(_valid_imp, 5, 2, 2, 20, 50, 1)

_master = MindData(
    str(_train_news),
    str(_train_imp),
    str(_valid_news),
    str(_valid_imp),
)

# ---------------------------------------------------------------------------
# The eight measured case files (built once at module level).
# ---------------------------------------------------------------------------
_case_params = [
    ("tiny", 500, 2, 2, 100, 1000, 10),
    ("small", 1000, 3, 3, 500, 5000, 11),
    ("medium", 2000, 5, 5, 1000, 10000, 12),
    ("many-lines-few-imps", 5000, 1, 1, 2000, 20000, 13),
    ("many-imps", 300, 50, 5, 100, 5000, 14),
    ("long-history", 500, 5, 100, 200, 10000, 15),
    ("many-users", 3000, 4, 4, 100000, 20000, 16),
    ("many-news", 2000, 8, 8, 1000, 500000, 17),
]
_case_files = []
for idx, (name, n, imp, hist, nu, nn, seed) in enumerate(_case_params):
    p = WORKDIR / f"case_{idx}_{name}.txt"
    _write_impressions(p, n, imp, hist, nu, nn, seed)
    _case_files.append((name, p))

# ---------------------------------------------------------------------------
# Edge-case files (checked only, never measured).
# ---------------------------------------------------------------------------
_check_empty = WORKDIR / "check_empty.txt"
_check_empty.write_text("")

_check_one = WORKDIR / "check_one.txt"
_check_one.write_text("0\tU1\t11/11/2019 1:05:00 PM\tN1 N2\tN3-1 N4-0\n")

_check_bad = WORKDIR / "check_bad.txt"
_check_bad.write_text("0\tU1\t11/11/2019 1:05:00 PM\tN1 N2\n")  # missing column


def _fresh_inst():
    """Return a fresh copy of the master instance (fresh maps, fresh lists)."""
    return copy.deepcopy(_master)


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def checks():
    return [
        ("empty", lambda: (_fresh_inst(), str(_check_empty), [])),
        ("one-line", lambda: (_fresh_inst(), str(_check_one), [])),
        ("malformed", lambda: (_fresh_inst(), str(_check_bad), [])),
    ]


def cases():
    return [
        (name, (lambda p=p: (_fresh_inst(), str(p), [])))
        for name, p in _case_files
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['many-lines-few-imps', 'many-users', 'many-news', 'medium']
_KEEP_CHECKS = ['empty', 'one-line', 'malformed']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
