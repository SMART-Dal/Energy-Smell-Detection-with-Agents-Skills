"""C7.S5 Unsimplified Operation -- reversing the whole string to compare it with
itself.

From Javad's BuiltInBehavior/IsStringPalindrome and IneffectiveComputation/
IsStringPalindrome, whose refactorings both go from `s == s[::-1]` to a
comparison of the two halves.

`s == s[::-1]` is the idiom, and it compares every character against its mirror
-- so each pair is examined twice, once from each end. Comparing `s[:half]`
against the reverse of `s[half:]` examines each pair once.

The trade is not free and the file exists to price it. `before` allocates one
copy of length n; `after` allocates three slices totalling 3n/2, and halves the
comparisons. Which side wins depends on whether the comparison or the
allocation dominates, and on where the first mismatch is -- `early-reject` is
the case where `before` allocates a full reversal to compare one character.

Javad's version omits the odd-length adjustment, so it compares a slice of
`half` characters against one of `half + 1` and reports every odd-length string
as not a palindrome. The `+ (len(text) % 2)` here is that correction; without
it the pair is not equivalent and nothing could be measured.
"""

def before(strings):
    hits = 0
    for text in strings:
        if text == text[::-1]:
            hits += 1
    return hits


def after(strings):
    hits = 0
    for text in strings:
        half = len(text) // 2
        if text[:half] == text[half + (len(text) % 2):][::-1]:
            hits += 1
    return hits


def _strings(count, width, palindromic):
    if palindromic:
        return ["ab" * (width // 2) + "ba" * (width // 2) for _ in range(count)]
    return [f"prefix{i}" + "x" * width for i in range(count)]


def cases():
    return [("palindromes",  lambda: (_strings(4_000, 500, True),)),
            ("early-reject", lambda: (_strings(4_000, 500, False),)),
            ("edge",         lambda: ([""],))]
