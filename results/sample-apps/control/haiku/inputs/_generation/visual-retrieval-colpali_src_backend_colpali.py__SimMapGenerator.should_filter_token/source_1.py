import re

# ---------------------------------------------------------------------------
# Module-level data.  The function under test is a pure regex test on a single
# token string, so the only way to give it real work is to hand it long tokens
# that exercise the different alternatives / lookaheads in its pattern.
# Strings are immutable, so the thunks can hand out the very same object every
# call without any copying.
# ---------------------------------------------------------------------------

_TOK_LT = "<" + "a" * 800_000                     # matches ^<.*$
_TOK_WS = " \t\n" * 200_000                       # 800k chars, matches ^\s+$
_TOK_PUNCT = "!" * 700_000                        # matches the punctuation alt
_TOK_WORD = "a" * 600_000                         # no alternative matches
_TOK_UNDER = "_" + "a" * 500_000                  # matches ^_.*$
_TOK_PUNCT_DIGIT = "!" * 399_999 + "7"            # digit at the very end
_TOK_WS_PUNCT = " " * 250_000 + "!" * 250_000     # mixed whitespace/punct
_TOK_QUESTION = "Question" + "a" * 400_000        # ^Question$ fails (not end)


def checks():
    return [
        ("empty-token", lambda: ("",)),
        ("question-exact", lambda: ("Question",)),
        ("none-token", lambda: (None,)),
    ]


def cases():
    return [
        ("lt-prefix-long", lambda: (_TOK_LT,)),
        ("whitespace-long", lambda: (_TOK_WS,)),
        ("punct-long", lambda: (_TOK_PUNCT,)),
        ("word-long", lambda: (_TOK_WORD,)),
        ("underscore-long", lambda: (_TOK_UNDER,)),
        ("punct-digit-end", lambda: (_TOK_PUNCT_DIGIT,)),
        ("ws-punct-mixed", lambda: (_TOK_WS_PUNCT,)),
        ("question-prefix-long", lambda: (_TOK_QUESTION,)),
    ]
