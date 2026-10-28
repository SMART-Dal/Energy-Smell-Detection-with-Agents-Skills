# Inputs for colbert-long/scripts/convert.py::remove_control_characters, generated outside the session: the 4 most
# expensive of 8 candidates that ran and repeated on the original.

import random
import unicodedata

from convert import remove_control_characters  # noqa: F401  (module under test)


# ---------------------------------------------------------------------------
# generators (module level: built once, never timed)
# ---------------------------------------------------------------------------

def _prose(chars, seed):
    """Word-shaped ASCII text with spaces and newlines."""
    rng = random.Random(seed)
    alpha = "abcdefghijklmnopqrstuvwxyz"
    out = []
    total = 0
    while total < chars:
        w = "".join(rng.choice(alpha) for _ in range(rng.randint(1, 12)))
        out.append(w)
        total += len(w) + 1
        if rng.random() < 0.02:
            out.append("\n")
        else:
            out.append(" ")
    return "".join(out)[:chars]


_CONTROL = ["\x00", "\x01", "\x07", "\x08", "\x0b", "\x0c", "\x1b", "\x1f",
            "\x7f", "\x80", "\x85", "\x9f", "\u2028", "\u2029"]


def _control_heavy(chars, seed):
    rng = random.Random(seed)
    alpha = "abcdefghijklmnopqrstuvwxyz "
    return "".join(rng.choice(_CONTROL) if rng.random() < 0.4
                   else rng.choice(alpha) for _ in range(chars))


def _unicode_mix(chars, seed):
    rng = random.Random(seed)
    pools = [
        [chr(c) for c in range(0x4E00, 0x4E00 + 250)],   # CJK
        [chr(c) for c in range(0x0300, 0x036F)],         # combining marks
        [chr(c) for c in range(0x00C0, 0x024F)],         # latin extended
        [chr(c) for c in range(0x0391, 0x03C9)],         # greek
        [chr(c) for c in range(0x0400, 0x04FF)],         # cyrillic
        [chr(c) for c in range(0x0590, 0x05FF)],         # hebrew
    ]
    flat = [c for p in pools for c in p] + [" ", "\n"]
    return "".join(rng.choice(flat) for _ in range(chars))


_ZERO_WIDTH = ["\u200b", "\u200c", "\u200d", "\u200e", "\u200f", "\ufeff",
               "\u00ad", "\u2060", "\u061c", "\u180e"]


def _zero_width(chars, seed):
    rng = random.Random(seed)
    alpha = "abcdefghijklmnopqrstuvwxyz "
    return "".join(rng.choice(_ZERO_WIDTH) if rng.random() < 0.35
                   else rng.choice(alpha) for _ in range(chars))


def _emoji(chars, seed):
    rng = random.Random(seed)
    pool = ([chr(c) for c in range(0x1F300, 0x1F650)]
            + [chr(c) for c in range(0x1F900, 0x1FA00)]
            + [chr(c) for c in range(0x2600, 0x27C0)])
    out = []
    n = 0
    while n < chars:
        if rng.random() < 0.3:
            out.append("\u200d")          # Cf joiner
            n += 1
        out.append(rng.choice(pool))
        n += 1
    return "".join(out)


def _long_line(chars, seed):
    rng = random.Random(seed)
    alpha = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(rng.choice(alpha) for _ in range(chars))


def _log(chars, seed):
    rng = random.Random(seed)
    out = []
    total = 0
    while total < chars:
        line = ("2024-%02d-%02dT%02d:%02d:%02d INFO [worker-%d] request %d "
                "completed in %dms\tstatus=%d\n"
                % (rng.randint(1, 12), rng.randint(1, 28), rng.randint(0, 23),
                   rng.randint(0, 59), rng.randint(0, 59), rng.randint(0, 9),
                   rng.randint(0, 10 ** 6), rng.randint(1, 5000),
                   rng.choice([200, 201, 404, 500])))
        out.append(line)
        total += len(line)
    return "".join(out)[:chars]


def _private_use(chars, seed):
    rng = random.Random(seed)
    pua = [chr(c) for c in range(0xE000, 0xE000 + 400)]
    alpha = "abcdefghijklmnopqrstuvwxyz "
    return "".join(rng.choice(pua) if rng.random() < 0.3
                   else rng.choice(alpha) for _ in range(chars))


# pre-built payloads (setup, not timed)
_ASCII_PROSE   = _prose(450_000, 0)
_CONTROL_HEAVY = _control_heavy(400_000, 1)
_UNICODE_MIX   = _unicode_mix(350_000, 2)
_ZERO_WIDTH    = _zero_width(400_000, 3)
_EMOJI         = _emoji(250_000, 4)
_LONG_LINE     = _long_line(500_000, 5)
_LOG           = _log(450_000, 6)
_PRIVATE_USE   = _private_use(350_000, 7)


def checks():
    return [
        ("empty",        lambda: ("",)),
        ("single-ctrl",  lambda: ("\n",)),
        ("none",         lambda: (None,)),
    ]


def cases():
    return [
        ("ascii-prose",   lambda: (_ASCII_PROSE,)),
        ("control-heavy", lambda: (_CONTROL_HEAVY,)),
        ("unicode-mix",   lambda: (_UNICODE_MIX,)),
        ("zero-width",    lambda: (_ZERO_WIDTH,)),
        ("emoji-zwj",     lambda: (_EMOJI,)),
        ("long-line",     lambda: (_LONG_LINE,)),
        ("log-multiline", lambda: (_LOG,)),
        ("private-use",   lambda: (_PRIVATE_USE,)),
    ]


# ---- the selection
_generated_cases, _generated_checks = cases, checks
_KEEP = ['long-line', 'unicode-mix', 'ascii-prose', 'log-multiline']
_KEEP_CHECKS = ['empty', 'single-ctrl', 'none']


def cases():
    return [c for c in _generated_cases() if c[0] in _KEEP]


def checks():
    return [c for c in _generated_checks() if c[0] in _KEEP_CHECKS]
