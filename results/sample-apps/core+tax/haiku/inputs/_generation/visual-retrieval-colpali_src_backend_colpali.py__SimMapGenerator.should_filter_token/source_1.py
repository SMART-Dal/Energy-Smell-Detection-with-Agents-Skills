import random

from backend.colpali import SimMapGenerator

# ---------------------------------------------------------------------------
# Long tokens so that a single call does measurable work.  The regex in
# should_filter_token uses greedy `.*` / `[^\w\s]+` / look-aheads that scan the
# whole token, so long strings exercise each branch with real cost.
# ---------------------------------------------------------------------------

_N = 300_000

_WORD = "a" * _N                                   # word chars only
_WORD_DIGIT = "a" * _N + "5"                       # digit near the end
_WS = " " * _N                                     # pure whitespace
_PUNCT = "!" * _N                                  # pure punctuation
_PUNCT_DIGIT = "!" * _N + "7"                      # punctuation + digit
_WORD_BAR = "a" * _N + "\u2581"                    # word chars + '▁'
_LT = "<" + "a" * _N                               # starts with '<'
_US = "_" + "a" * _N                               # starts with '_'


def checks():
    return [
        ("empty", lambda: ("",)),
        ("single-bar", lambda: ("\u2581",)),
        ("none-token", lambda: (None,)),
    ]


def cases():
    return [
        ("long-word", lambda: (_WORD,)),
        ("long-word-digit", lambda: (_WORD_DIGIT,)),
        ("long-whitespace", lambda: (_WS,)),
        ("long-punctuation", lambda: (_PUNCT,)),
        ("long-punctuation-digit", lambda: (_PUNCT_DIGIT,)),
        ("long-word-bar", lambda: (_WORD_BAR,)),
        ("long-lt", lambda: (_LT,)),
        ("long-underscore", lambda: (_US,)),
    ]
