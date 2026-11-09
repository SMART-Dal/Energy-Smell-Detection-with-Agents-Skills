import importlib
import random

_mod = importlib.import_module('create-github-comments')
is_voter_comment = _mod.is_voter_comment
HEADER = _mod.HEADER


def _filler_lines(n, seed, long_lines=False):
    """Realistic-ish GitHub comment filler lines."""
    rng = random.Random(seed)
    out = []
    if long_lines:
        for i in range(n):
            out.append(f"line {i} " + "x" * 4000)
        return out
    for i in range(n):
        r = rng.random()
        if r < 0.25:
            out.append(
                f"- @user{rng.randrange(10**7)} contributed "
                f"{rng.randrange(1, 60)} PRs and code reviews"
            )
        elif r < 0.50:
            out.append(
                f"Comment {i}: this change touches the collector pipeline "
                f"and needs another look before merge."
            )
        elif r < 0.65:
            out.append("")
        elif r < 0.80:
            out.append(f"### Subsection {i}")
        else:
            out.append(f"> quoted text from an earlier comment, index {i}")
    return out


def _body(first_line, n, seed, long_lines=False):
    lines = [first_line]
    lines.extend(_filler_lines(n, seed, long_lines))
    return "\n".join(lines)


def _body_with_header_at(n_before, n_after, seed):
    lines = _filler_lines(n_before, seed)
    lines.append(HEADER)
    lines.extend(_filler_lines(n_after, seed + 1))
    return "\n".join(lines)


# ---- module-level data, built once, never timed ----
B_HEADER_20K = _body(HEADER, 20_000, 0)
B_HEADER_200K = _body(HEADER, 200_000, 1)
B_HEADER_LATE = _body_with_header_at(5_000, 90_000, 2)
B_NO_HEADER = _body("Discussion about the governance committee election process.", 120_000, 3)
B_PADDED = _body("   " + HEADER + "  \t", 80_000, 4)
B_TRUNCATED = _body(HEADER[:-12], 60_000, 5)
B_LONG_LINES = _body(HEADER, 1_500, 6, long_lines=True)
B_BLANK_FIRST = "\n" + HEADER + "\n" + "\n".join(_filler_lines(70_000, 7))


def checks():
    return [
        ("empty-string", lambda: ("",)),
        ("none-body", lambda: (None,)),
        ("whitespace-only", lambda: ("   \n \t \n",)),
    ]


def cases():
    return [
        ("header-first-20k", lambda: (B_HEADER_20K,)),
        ("header-first-200k", lambda: (B_HEADER_200K,)),
        ("header-late-miss", lambda: (B_HEADER_LATE,)),
        ("no-header-long", lambda: (B_NO_HEADER,)),
        ("header-padded", lambda: (B_PADDED,)),
        ("header-truncated", lambda: (B_TRUNCATED,)),
        ("header-long-lines", lambda: (B_LONG_LINES,)),
        ("blank-first-line", lambda: (B_BLANK_FIRST,)),
    ]
