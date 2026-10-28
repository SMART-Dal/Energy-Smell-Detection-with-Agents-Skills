import random

from dxpy.utils.completer import ListCompleter

# ---------------------------------------------------------------------------
# Data generation (module level, never timed)
# ---------------------------------------------------------------------------

_PLAIN_PREFIXES = ['app', 'applet', 'workflow', 'tool', 'data', 'file',
                   'globalworkflow', 'read', 'write', 'run']


def _plain(n, seed):
    """Plain word-like completions, as used for --category / suggestions."""
    rng = random.Random(seed)
    out = []
    for i in range(n):
        p = _PLAIN_PREFIXES[rng.randrange(len(_PLAIN_PREFIXES))]
        out.append('%s-%07d-%06d' % (p, i, rng.randrange(1000000)))
    return out


def _paths(n, seed):
    """DX-style completions of the form project:/folder/name (contain colons)."""
    rng = random.Random(seed)
    out = []
    for i in range(n):
        proj = 'project-%02d' % rng.randrange(20)
        folder = '/folder%d' % rng.randrange(10)
        out.append('%s:%s/file%07d.txt' % (proj, folder, i))
    return out


_PLAIN = _plain(200000, 0)
_PATHS = _paths(200000, 1)

# Smaller slices used for the "matches everything" cases so that the number of
# returned matches stays well under 100k.
_PLAIN_SMALL = _PLAIN[:60000]
_PATHS_SMALL = _PATHS[:60000]

_LINE_ALL = 'dx find apps --name '
_LINE_RECOMPUTE = 'dx find apps --name app'


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------

def checks():
    return [
        ("empty-completions", lambda: (ListCompleter([]), "a", len("a"), "a", "")),
        ("single-element", lambda: (ListCompleter(["true"]), "t", len("t"), "t", "")),
        ("colon-no-match", lambda: (ListCompleter(["alpha", "beta"]), "x:y", len("x:y"), "x:y", "")),
    ]


def cases():
    return [
        # prefix recomputed from the line, matches a good chunk of the list
        ("plain-app",
         lambda: (ListCompleter(list(_PLAIN)), "app", len("app"), "app", "")),

        # full scan, no matches at all
        ("plain-no-match",
         lambda: (ListCompleter(list(_PLAIN)), "zzz", len("zzz"), "zzz", "")),

        # line ends with a space -> given prefix ("") is kept, everything matches
        ("plain-all",
         lambda: (ListCompleter(list(_PLAIN_SMALL)), _LINE_ALL, len(_LINE_ALL), "", "")),

        # prefix comes from the last word of a longer command line
        ("plain-recompute",
         lambda: (ListCompleter(list(_PLAIN)), _LINE_RECOMPUTE, len(_LINE_RECOMPUTE),
                  "IGNORED", "")),

        # colon prefix -> matches get colon-stripped
        ("path-colon",
         lambda: (ListCompleter(list(_PATHS)), "project-03:", len("project-03:"),
                  "project-03:", "")),

        # colon prefix matching everything -> colon-strip loop over all matches
        ("path-all-colon",
         lambda: (ListCompleter(list(_PATHS_SMALL)), "project-", len("project-"),
                  "project-", "")),

        # deeper colon prefix, few matches but full scan
        ("path-folder",
         lambda: (ListCompleter(list(_PATHS)), "project-03:/folder5/",
                  len("project-03:/folder5/"), "project-03:/folder5/", "")),

        # single plain prefix family
        ("plain-data",
         lambda: (ListCompleter(list(_PLAIN)), "data-", len("data-"), "data-", "")),
    ]
