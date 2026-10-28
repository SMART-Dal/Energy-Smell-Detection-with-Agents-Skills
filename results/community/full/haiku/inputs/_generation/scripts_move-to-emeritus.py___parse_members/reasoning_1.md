We need to write checks() and cases() for `_parse_members(text)`. It's a pure function: parses text with regex, returns list of dicts.

We need 8 measured cases with realistic README section text. Realistic: GitHub community README sections with member entries like `- [Name](https://github.com/username), extra info`.

The regex: `^[-*+] \[([^\]]+)\]\(https://github\.com/([^)]+)\)(?:,\s*(.+))?$` MULTILINE.

So lines starting with -, *, or +, then `[name](https://github.com/username)`, optionally `, something`.

We need diverse inputs: many members, few members, lines that don't match (misses), different markers (-, *, +), names with brackets? names with special chars, usernames with slashes? `[^)]+` allows anything but `)`. Trailing text after comma.

Also lines that look similar but don't match (misses) — e.g. links to other domains, missing comma, etc. The function does work proportional to text length (regex scanning) plus matches.

Let's design 8 cases:

1. Typical section: ~2000 member lines with "- " marker, some with trailing text.
2. Large section: ~20000 member lines, mixed markers.
3. Mostly non-matching lines (misses) mixed with few matches — large text, stress regex scanning.
4. Dense matches with long names/usernames and trailing descriptions (long lines).
5. Entries with `*` and `+` markers, indented? Wait — regex has `^[-*+]` with MULTILINE, so indentation would break match. Real README sections might have indented lists? The repo's own README... but we don't know. Keep to non-indented.
6. Lines with tricky content: names containing `]`? `[^\]]+` so no. Names containing parentheses, unicode, emoji. Usernames with hyphens, numbers.
7. Entries where the optional trailing part is long, and entries without trailing part.
8. Many duplicate entries (same username repeated) — duplicates are realistic in stress.

Also lines that almost match: `- [Name](https://github.com/user),` with trailing comma and nothing after? `(?:,\s*(.+))?` requires at least one char after comma+spaces. So `- [Name](https://github.com/user),` alone doesn't match (the `,` would be leftover, and `$` requires end). Actually the regex: after `\)` optional group `,\s*(.+)`. If the line is `- [Name](https://github.com/user),` then the optional group can't match (needs `.+`), so the regex would try to match ending at `)` but then `$` requires end of line — the `,` remains, so no match. Good miss case.

Also `http://` instead of https, `www.github.com`, missing `https://`.

Let's think about performance: regex finditer over a large text. Each case should take ~1ms-200ms. Python regex scanning ~ maybe 10-50 MB/s for this pattern. To reach ~100ms we'd need maybe 5-10 MB of text. Let's aim for a few MB max. 20000 lines * ~80 chars = 1.6 MB. That's probably ~50-100 ms. Let's keep sizes moderate: total data under 100MB, fine.

Actually let's be careful: the regex is applied with MULTILINE and finditer; scanning is linear-ish. Let's test mentally: pattern starts with `^[-*+]` — the engine will scan for line starts with those chars. Should be reasonably fast.

Let's build helper functions.

Important: the function doesn't mutate input; text is a str immutable. So thunks can return the same string each time — but the thunk must return args; returning the same string object is fine since str is immutable and function doesn't change it. Actually the harness renders arguments before/after to check they didn't change — for a str, fine.

But wait: "keep a thunk cheap next to one call: build large data once, in module-level code, and have the thunk return it — or a copy if the function changes it". str is immutable, so return it directly.

Now, checks(): 2-3 small edge inputs: empty string, text with no matches, maybe a line that almost matches. These may raise — they don't.

Let's write:

```python
import importlib
import random

_parse_members = importlib.import_module('move-to-emeritus')._parse_members
```

Wait, the task says "Import it as `_parse_members = importlib.import_module('move-to-emeritus')._parse_members`". So we do that. But is the module importable? `scripts/move-to-emeritus.py` — the import machinery needs `scripts` on sys.path presumably, or the harness handles it. The task says import exactly as shown. We'll do that. But careful: importing the module runs top-level code — it imports urllib etc., defines functions; main() is presumably guarded by `if __name__ == "__main__"`. Should be fine.

Hmm, but the module name has a hyphen — importlib.import_module works with arbitrary names if findable on sys.path. The harness presumably sets sys.path to include scripts dir. We just follow instructions.

Now data generation.

Let me define a helper to build a README section text.

Realistic member entry format from the repo (community repo README): something like:

```
- [John Doe](https://github.com/johndoe), John Doe
```

Actually in kubernetes/community README, entries look like:
```
- [Name](https://github.com/username)
```
or with additional info.

Let's generate names and usernames with a fixed rng.

Design 8 cases:

1. "typical-2k": 2000 matching entries, marker "-", ~30% with trailing ", description".
2. "large-20k-mixed-markers": 20000 entries with markers cycling -, *, +, some with trailing text.
3. "mostly-misses": 15000 lines, only ~200 matches; misses are lines with markdown links to other sites, plain text, headers, blank lines.
4. "long-lines": 3000 entries with long names (unicode, emoji) and long trailing descriptions (~200 chars each).
5. "no-trailing": 15000 entries without trailing text (short lines) — tests the optional group absent path.
6. "all-trailing": 8000 entries all with trailing text.
7. "duplicates": 10000 entries, only 50 distinct usernames repeated — duplicates.
8. "near-miss-heavy": large text with many almost-matching lines (wrong scheme, missing paren, trailing comma, indented) plus some matches.

Hmm, we want each to do "substantial and different work". Also keep total under limits: outputs (list of dicts) under 100k values. Each dict has 3 values; 20000 entries = 60000 values, ok. But "keep what it returns under about 100 000 values" — 20000 dicts * 3 = 60000, fine. Let's cap matches at ~20000.

Actually careful: for case 2 with 20000 matches, output is 20000 dicts. Values: 3 per dict = 60000. Fine.

Also arguments rendered before/after: text of ~2MB — the render is of the argument (a str), fine.

Let's estimate time. Regex finditer over 2MB text: probably ~20-50 ms. Good.

Let's make sure the largest case is not over 1s. 20000 lines * 80 chars = 1.6MB. Should be fine.

Let me write the generation code.

```python
import importlib
import random

_parse_members = importlib.import_module('move-to-emeritus')._parse_members

_FIRST = ["Alice", "Bob", ...]
```

Better: generate names from word lists with rng.

```python
_WORDS = ["al", "be", "car", "dan", "eve", ...]
```

Simpler: build names as f"{first} {last}" from random choice of syllables.

Let me write helper:

```python
def _username(rng):
    return "".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789-") for _ in range(rng.randint(3, 15))).strip("-")
```

Hmm usernames can't start/end with hyphen; not important for regex.

Names: include unicode and emoji occasionally for diversity.

Let's write:

```python
_NAMES = [
    "Alice Smith", "Bob Jones", "Carol White", "David Brown", "Eve Davis",
    "Frank Miller", "Grace Lee", "Henry Wilson", "Ivy Chen", "Jack Taylor",
    "Kara Novak", "Liam O'Brien", "Mia García", "Noah Müller", "Olivia Rossi",
    "Pablo Fernández", "Quinn Adams", "Rosa Kim", "Sam Patel", "Tina Nguyen",
    "Umar Hassan", "Vera Petrova", "Wes Clark", "Xena Papadopoulos", "Yuki Tanaka",
    "Zara Ali", "Zoë Ångström", "José María López", "李雷", "王小明",
    "🦊 Fox Dev", "Ann-Marie O'Neil", "Björn Þórsson", "Nguyễn Văn A",
]
```

Names with `]`? Not allowed by regex `[^\]]+`. Names with `[`? `[^\]]+` allows `[`. Let's include a name with `[` maybe. Fine.

Trailing text: descriptions like "emeritus since 2023", "SIG Docs lead", etc.

Now the cases.

Let me write generation functions returning text.

```python
def _entry(rng, marker="-", trailing=True, name=None, user=None, desc_len=None):
    name = name or rng.choice(_NAMES)
    user = user or _username(rng)
    line = f"{marker} [{name}](https://github.com/{user})"
    if trailing:
        desc = " ".join(rng.choice(_DESC_WORDS) for _ in range(...))
        line += f", {desc}"
    return line
```

Wait, the trailing part is captured but not used in output except... actually the output dict only has name, username, line. The trailing group isn't used. So trailing text only affects line length and regex work.

OK.

Now build texts:

Case 1 typical:
```python
def _typical(n, seed, marker="-", trailing_ratio=0.3):
    rng = random.Random(seed)
    lines = ["## Emeritus Maintainers", ""]
    for i in range(n):
        lines.append(_entry(rng, marker, rng.random() < trailing_ratio))
    return "\n".join(lines)
```

Case 2 mixed markers: markers cycle.

Case 3 mostly misses: lines like:
- `- [Name](http://github.com/user)` (http)
- `- [Name](https://gitlab.com/user)`
- `- Name (https://github.com/user)` 
- `- [Name](https://github.com/user),` (trailing comma, no desc) -> miss
- `  - [Name](https://github.com/user)` (indented) -> miss
- `* [Name] (https://github.com/user)` space before paren -> miss
- plain text lines
- headers
- blank lines

Case 4 long lines: long names and long descriptions.

Case 5 no trailing: all entries without trailing.

Case 6 all trailing with long-ish descriptions.

Case 7 duplicates: 50 usernames repeated, names vary or same.

Case 8 near-miss heavy + matches: mix.

Also maybe a case with unicode-heavy names.

We need exactly 8. Let's finalize:

1. `typical-2k` — 2000 entries, "-", 30% trailing.
2. `large-mixed-markers-20k` — 20000 entries, markers cycling.
3. `mostly-misses-15k` — 15000 lines, ~150 matches.
4. `long-lines-3k` — 3000 entries with long names + long trailing descriptions.
5. `no-trailing-15k` — 15000 entries without trailing text.
6. `unicode-names-8k` — 8000 entries with unicode/emoji names and varied trailing.
7. `duplicates-10k` — 10000 entries, 40 distinct usernames.
8. `near-miss-heavy-12k` — 12000 lines, half near-misses, half matches.

Total matches: 2000+20000+150+3000+15000+8000+10000+6000 = ~64k dicts across all cases. Each case individually under 100k values? Case 2: 20000 dicts * 3 = 60000 values. OK. Case 5: 15000*3=45000. Case 7: 10000*3=30000. Fine.

Time: case 2 with 20000 lines ~1.6MB. Let's estimate regex speed. The pattern `^[-*+] \[...` — Python's re with MULTILINE. For each position, it checks `^` (line start) then `[-*+]`. Actually the engine scans char by char; at each position it tries to match. The `^` in MULTILINE is a zero-width assertion checking preceding char is `\n` or start. This is fairly fast but scanning 1.6MB char by char... Python re is C-level, maybe 100-300 MB/s for simple scanning. So ~10ms. Hmm, that might be too fast? Requirement says one call roughly 1ms-200ms. 10ms is fine (above 1ms). But to be safe let's make case 2 bigger: 40000 entries? That's 3.2MB, output 40000 dicts = 120000 values > 100k limit. Hmm, limit is "under about 100 000 values" for what it returns. 40000 dicts → 120k values. Risky.

Alternative: make the text longer without more matches — e.g., long trailing descriptions. Case 4 does that.

Actually the "work" measured is time; we need cases that take meaningful time. Let's just make case 2 with 25000 entries (~2MB). Output 75000 values, under 100k. Fine.

Actually let me reconsider: what does "values" mean? Probably len of rendered output. 25000 dicts each with 3 strings → 75000 leaf values. OK.

Let's also add long descriptions in case 2 to increase text size.

Let me be a bit generous but safe: max matches per case ~25000.

Let's now write the code carefully.

```python
import importlib
import random

_parse_members = importlib.import_module('move-to-emeritus')._parse_members

_NAMES = [...]

_DESC_WORDS = ["maintainer", "emeritus", "since", "2019", "SIG", "Docs", "release", "team", "lead", "contributor", "Kubernetes", "steering", "committee", "alumni", "emeritus", "reviewer", "approver", "owner"]

def _username(rng):
    n = rng.randint(3, 16)
    s = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789-") for _ in range(n))
    return s.strip("-") or "user"

def _desc(rng, words):
    return " ".join(rng.choice(_DESC_WORDS) for _ in range(words))
```

Entry builder:

```python
def _entry(rng, marker, trailing):
    name = rng.choice(_NAMES)
    user = _username(rng)
    line = f"{marker} [{name}](https://github.com/{user})"
    if trailing:
        line += ", " + _desc(rng, rng.randint(1, 6))
    return line
```

Hmm but for case 4 we want long names/descriptions. We'll write separate builders.

Now, one subtlety: `_username` might produce duplicates; that's fine.

Let's write each case builder.

Case 1:
```python
def _case_typical():
    rng = random.Random(0)
    lines = ["# Emeritus Maintainers", "", "The following are emeritus:", ""]
    for _ in range(2000):
        lines.append(_entry(rng, "-", rng.random() < 0.3))
    lines.append("")
    return "\n".join(lines)
```

Case 2 mixed markers:
```python
def _case_large_mixed():
    rng = random.Random(1)
    markers = "-*+"
    lines = ["## Section", ""]
    for i in range(25000):
        m = markers[i % 3]
        lines.append(_entry(rng, m, rng.random() < 0.5))
    return "\n".join(lines)
```

Wait, cycling markers is a pattern — "Avoid uniformity or patterns ... that a simple trick could exploit". The marker cycle is a pattern but the function doesn't exploit it; still, let's randomize marker choice.

```python
m = rng.choice("-*+")
```

Case 3 mostly misses:
```python
def _case_mostly_misses():
    rng = random.Random(2)
    lines = []
    for i in range(15000):
        r = rng.random()
        if r < 0.01:
            lines.append(_entry(rng, "-", rng.random() < 0.5))
        elif r < 0.2:
            lines.append(f"- [{rng.choice(_NAMES)}](http://github.com/{_username(rng)})")
        elif r < 0.35:
            lines.append(f"- [{rng.choice(_NAMES)}](https://gitlab.com/{_username(rng)})")
        elif r < 0.5:
            lines.append(f"- [{rng.choice(_NAMES)}](https://github.com/{_username(rng)}),")
        elif r < 0.65:
            lines.append(f"  - [{rng.choice(_NAMES)}](https://github.com/{_username(rng)})")
        elif r < 0.8:
            lines.append(f"* [{rng.choice(_NAMES)}] (https://github.com/{_username(rng)})")
        elif r < 0.9:
            lines.append("")
        else:
            lines.append(f"Some prose about {rng.choice(_NAMES)} and their work.")
    return "\n".join(lines)
```

That gives ~150 matches. Good.

Hmm wait: `- [Name](https://github.com/user),` — does it match? Regex: `^[-*+] \[([^\]]+)\]\(https://github\.com/([^)]+)\)(?:,\s*(.+))?$`. After `)` we have `,` then end. Optional group requires `,\s*(.+)` — `.+` needs at least one char after optional whitespace. `,` then end: `\s*` matches empty, `.+` needs ≥1 char, none. So group fails; then the optional group is skipped, and `$` must match at position after `)`. But there's `,` before end. `$` in MULTILINE matches at end of string or before newline. Position after `)` is not before newline (there's `,`). So no match. Good.

Case 4 long lines:
```python
def _case_long_lines():
    rng = random.Random(3)
    lines = []
    for _ in range(3000):
        name = " ".join(rng.choice(_NAMES) for _ in range(rng.randint(3, 8)))
        user = _username(rng)
        desc = _desc(rng, rng.randint(30, 60))
        lines.append(f"- [{name}](https://github.com/{user}), {desc}")
    return "\n".join(lines)
```

Name with multiple names joined — fine.

Case 5 no trailing:
```python
def _case_no_trailing():
    rng = random.Random(4)
    lines = []
    for _ in range(15000):
        lines.append(_entry(rng, "-", False))
    return "\n".join(lines)
```

Case 6 unicode names:
```python
_UNICODE_NAMES = ["José María López", "李雷", "王小明", "Björn Þórsson", "Nguyễn Văn A", "🦊 Fox Dev", "Zoë Ångström", "Ann-Marie O'Neil", "Müller, Hans", "Пётр Иванов", "محمد علي", "שלום כהן", "Emoji 🚀 Rocket", "C++ Guru", "a[b]c", "Name (with parens)"]
```

Hmm "Name (with parens)" — the name group is `[^\]]+` inside `[...]`, so parens fine. "a[b]c" — `[` allowed, `]` not. So avoid `]` in names. "a[b]c" has `]`? No, it's `a[b]c` — contains `[` and `]`. `]` would terminate the group. Actually `[^\]]+` matches up to first `]`. So `[a[b]c]` would match name as `a[b` and then require `](` but next char is `c` → fail. So avoid `]` in names. Let's not include that.

Case 6:
```python
def _case_unicode():
    rng = random.Random(5)
    lines = []
    for _ in range(8000):
        name = rng.choice(_UNICODE_NAMES)
        user = _username(rng)
        if rng.random() < 0.5:
            lines.append(f"- [{name}](https://github.com/{user}), {_desc(rng, rng.randint(1, 4))}")
        else:
            lines.append(f"* [{name}](https://github.com/{user})")
    return "\n".join(lines)
```

Case 7 duplicates:
```python
def _case_duplicates():
    rng = random.Random(6)
    users = [_username(rng) for _ in range(40)]
    lines = []
    for i in range(10000):
        u = users[i % 40]  # pattern... use rng.choice
        ...
```

Use rng.choice(users). Names vary. This tests duplicates in output.

Case 8 near-miss heavy:
```python
def _case_near_miss():
    rng = random.Random(7)
    lines = []
    for i in range(12000):
        if i % 2 == 0:
            lines.append(_entry(rng, rng.choice("-*+"), rng.random() < 0.5))
        else:
            # near miss variants
            ...
```

Hmm, alternating is a pattern. Use rng.random().

Let me write near-miss variants:
- `- [Name](https://github.com/user) ` (trailing space) → does it match? `$` matches before newline; trailing space means `$` fails... Actually `$` in MULTILINE matches at end of line, i.e., before `\n`. A trailing space is before `$`? The line is `... ) ` then `\n`. `$` matches at position before `\n`, which is after the space. So the regex would need to consume the space — it can't. So no match. Good near-miss.
- `- [Name](https://github.com/user), ` (comma space) → optional group `,\s*(.+)` — `\s*` consumes the space, `.+` needs ≥1 char, none before newline. Fails. Then `$` after `)`: no. Miss.
- `- [Name](https://github.com/user) extra` → after `)`, ` extra` — optional group doesn't start with comma, so skipped, `$` fails. Miss.
- `- [Name](https://github.com/user),extra` → matches! `,\s*(.+)` with `\s*` empty, `.+` = "extra". So it's a match, not a miss. Careful.
- `+ [Name](https://github.com/user))` → extra `)` — `[^)]+` for username stops at first `)`; then after `)` there's another `)` → `$` fails. Miss.
- `- [Name](https://github.com/)` → username group `[^)]+` needs ≥1 char, empty → fail. Miss.
- `- [](https://github.com/user)` → name `[^\]]+` needs ≥1 → fail. Miss.
- `- [Name](https://github.com/user/repo)` → username `[^)]+` matches `user/repo` → match. Interesting: username with slash. That's a match, realistic-ish? Not really but fine as a match variant.
- `- [Name](HTTPS://github.com/user)` → case-sensitive, miss.
- `- [Name](https://github.com/user),` → miss as discussed.

OK.

Now, one thing to be careful about: the harness renders arguments before/after each call to check for mutation. For a large string, rendering could be expensive but that's not timed presumably... Actually "Its arguments are rendered before and after each call to see whether it changed them" — that's harness overhead, not our concern, but keep data reasonable.

Now checks():

```python
def checks():
    return [
        ("empty", lambda: ("",)),
        ("no-members", lambda: ("# Title\n\nSome prose.\n",)),
        ("single-member", lambda: ("- [Alice](https://github.com/alice)\n",)),
    ]
```

Maybe include an odd type: `None`? The function would raise TypeError on `re.finditer(None)` → "expected string or bytes-like object". That's allowed ("These may raise"). Let's include one: ("none-text", lambda: (None,)). Hmm, but "checked only for identical behaviour" — both original and modified raise the same. It's fine. But maybe safer to keep to strings plus one odd. Let's include None as third. Actually let's do:

1. empty string
2. no matches text
3. None (odd type)

That's 3.

Now, module-level: we build the texts once at module level? The instructions say build large data once in module-level code and have the thunk return it. But building at module level runs at import time — that's fine (not timed). However, building 8 large texts at import might take some time (under 10s). Let's estimate: generating ~100k lines with rng — maybe 0.5s. Fine.

Alternatively, build lazily in the thunk — but then each thunk call rebuilds, which is expensive next to the call. The instructions: "build large data once, in module-level code, and have the thunk return it". So module-level.

But careful: thunks are called before timing for each repetition? "Thunks run before the timing starts" — each call gets the arguments of its own thunk call. If the thunk returns the module-level string, it's cheap. Good.

Let me structure: module-level compute `_TEXTS = {...}` then cases return `lambda: (_TEXTS["typical"],)`.

But building all 8 texts at import time even if not used — fine.

Actually, to be safe about import cost, we can build them at module level directly.

Let me now write the final code.

Also need to double check: `importlib.import_module('move-to-emeritus')` — the module has a hyphen; importlib handles it if the file is on sys.path as `move-to-emeritus.py`. The harness presumably sets that up. We just follow the given import line.

Hmm, but should we also handle the case where the module is in `scripts/` and needs sys.path? The task says "Import the repository's modules exactly as shown in the task." So use exactly that line.

Let me write:

```python
import importlib
import random

_parse_members = importlib.import_module('move-to-emeritus')._parse_members
```

Wait — does importing the module execute `main()`? Only if `if __name__ == "__main__"`. Presumably. Fine.

Now let's write the whole thing.

```python
import importlib
import random

_parse_members = importlib.import_module('move-to-emeritus')._parse_members

_NAMES = [
    "Alice Smith", "Bob Jones", "Carol White", "David Brown", "Eve Davis",
    "Frank Miller", "Grace Lee", "Henry Wilson", "Ivy Chen", "Jack Taylor",
    "Kara Novak", "Liam O'Brien", "Mia Garcia", "Noah Muller", "Olivia Rossi",
    "Pablo Fernandez", "Quinn Adams", "Rosa Kim", "Sam Patel", "Tina Nguyen",
    "Umar Hassan", "Vera Petrova", "Wes Clark", "Xena Papadopoulos",
    "Yuki Tanaka", "Zara Ali", "Zoe Angstrom", "Jose Maria Lopez",
    "Ann-Marie O'Neil", "Bjorn Thorsson", "Nguyen Van A", "Mary-Jane Watson",
]

_UNICODE_NAMES = [
    "José María López", "李雷", "王小明", "Björn Þórsson", "Nguyễn Văn A",
    "🦊 Fox Dev", "Zoë Ångström", "Ann-Marie O'Neil", "Müller, Hans",
    "Пётр Иванов", "محمد علي", "שלום כהן", "Emoji 🚀 Rocket",
    "C++ Guru", "Name (with parens)", "O'Brien, Sean", "Ana-Maria Popescu",
    "François Lefèvre", "李小龙", "山田太郎",
]

_DESC_WORDS = [
    "maintainer", "emeritus", "since", "2019", "2020", "SIG", "Docs",
    "release", "team", "lead", "contributor", "Kubernetes", "steering",
    "committee", "alumni", "reviewer", "approver", "owner", "and", "the",
    "working", "group", "subproject", "emeritus", "inactive", "former",
]

_ALNUM = "abcdefghijklmnopqrstuvwxyz0123456789-"


def _username(rng):
    n = rng.randint(3, 16)
    s = "".join(rng.choice(_ALNUM) for _ in range(n)).strip("-")
    return s or "user"


def _desc(rng, words):
    return " ".join(rng.choice(_DESC_WORDS) for _ in range(words))


def _entry(rng, marker, trailing):
    name = rng.choice(_NAMES)
    user = _username(rng)
    line = f"{marker} [{name}](https://github.com/{user})"
    if trailing:
        line += ", " + _desc(rng, rng.randint(1, 6))
    return line
```

Then the builders.

```python
def _build_typical():
    rng = random.Random(0)
    lines = ["# Emeritus Maintainers", "", "The following members are emeritus:", ""]
    for _ in range(2000):
        lines.append(_entry(rng, "-", rng.random() < 0.3))
    lines.append("")
    return "\n".join(lines)


def _build_large_mixed():
    rng = random.Random(1)
    lines = ["## Emeritus", ""]
    for _ in range(25000):
        lines.append(_entry(rng, rng.choice("-*+"), rng.random() < 0.5))
    return "\n".join(lines)


def _build_mostly_misses():
    rng = random.Random(2)
    lines = ["# Section", ""]
    for _ in range(15000):
        r = rng.random()
        name = rng.choice(_NAMES)
        user = _username(rng)
        if r < 0.01:
            lines.append(_entry(rng, "-", rng.random() < 0.5))
        elif r < 0.18:
            lines.append(f"- [{name}](http://github.com/{user})")
        elif r < 0.32:
            lines.append(f"- [{name}](https://gitlab.com/{user})")
        elif r < 0.46:
            lines.append(f"- [{name}](https://github.com/{user}),")
        elif r < 0.60:
            lines.append(f"  - [{name}](https://github.com/{user})")
        elif r < 0.72:
            lines.append(f"* [{name}] (https://github.com/{user})")
        elif r < 0.82:
            lines.append(f"- [{name}](https://github.com/{user}) ")
        elif r < 0.90:
            lines.append("")
        else:
            lines.append(f"Some prose about {name} and their past work on the project.")
    return "\n".join(lines)
```

Wait, `- [{name}](https://github.com/{user}) ` with trailing space — no match, good.

```python
def _build_long_lines():
    rng = random.Random(3)
    lines = []
    for _ in range(3000):
        name = " ".join(rng.choice(_NAMES) for _ in range(rng.randint(3, 8)))
        user = _username(rng)
        desc = _desc(rng, rng.randint(30, 60))
        lines.append(f"- [{name}](https://github.com/{user}), {desc}")
    return "\n".join(lines)


def _build_no_trailing():
    rng = random.Random(4)
    lines = []
    for _ in range(15000):
        lines.append(_entry(rng, "-", False))
    return "\n".join(lines)


def _build_unicode():
    rng = random.Random(5)
    lines = []
    for _ in range(8000):
        name = rng.choice(_UNICODE_NAMES)
        user = _username(rng)
        if rng.random() < 0.5:
            lines.append(f"- [{name}](https://github.com/{user}), {_desc(rng, rng.randint(1, 4))}")
        else:
            lines.append(f"* [{name}](https://github.com/{user})")
    return "\n".join(lines)


def _build_duplicates():
    rng = random.Random(6)
    users = [_username(rng) for _ in range(40)]
    lines = []
    for _ in range(10000):
        user = rng.choice(users)
        name = rng.choice(_NAMES)
        marker = rng.choice("-*+")
        if rng.random() < 0.4:
            lines.append(f"{marker} [{name}](https://github.com/{user}), {_desc(rng, rng.randint(1, 3))}")
        else:
            lines.append(f"{marker} [{name}](https://github.com/{user})")
    return "\n".join(lines)


def _build_near_miss():
    rng = random.Random(7)
    lines = []
    for _ in range(12000):
        name = rng.choice(_NAMES)
        user = _username(rng)
        r = rng.random()
        if r < 0.45:
            lines.append(_entry(rng, rng.choice("-*+"), rng.random() < 0.5))
        elif r < 0.55:
            lines.append(f"- [{name}](https://github.com/{user}), ")
        elif r < 0.63:
            lines.append(f"- [{name}](https://github.com/{user}) trailing")
        elif r < 0.71:
            lines.append(f"+ [{name}](https://github.com/{user}))")
        elif r < 0.79:
            lines.append(f"- [{name}](https://github.com/)")
        elif r < 0.86:
            lines.append(f"- [](https://github.com/{user})")
        elif r < 0.93:
            lines.append(f"- [{name}](HTTPS://github.com/{user})")
        else:
            lines.append(f"- [{name}](https://github.com/{user}/{_username(rng)})")
    return "\n".join(lines)
```

Hmm, `- [Name](https://github.com/user) trailing` — after `)`, " trailing". Optional group requires `,`. So skipped; `$` fails. Miss. Good.

`- [Name](https://github.com/user))` — username `[^)]+` matches "user" (stops at first `)`), then `\)` matches first `)`, then optional group: next char is `)` not `,` → skipped; `$` at position before second `)`? No, `$` requires end of line. Fails. Miss. Good.

`- [Name](https://github.com/)` — username needs ≥1 char; the `)` immediately after `/` → fail. Miss.

`- [](https://github.com/user)` — name `[^\]]+` needs ≥1; `]` immediately → fail. Miss.

`- [Name](HTTPS://github.com/user)` — literal `https://` lowercase required; "HTTPS" fails. Miss.

`- [Name](https://github.com/user/repo)` — username `[^)]+` matches "user/repo" → match. Good.

Now the cases function:

```python
_TEXTS = {
    "typical": _build_typical(),
    "large-mixed": _build_large_mixed(),
    "mostly-misses": _build_mostly_misses(),
    "long-lines": _build_long_lines(),
    "no-trailing": _build_no_trailing(),
    "unicode": _build_unicode(),
    "duplicates": _build_duplicates(),
    "near-miss": _build_near_miss(),
}


def cases():
    return [
        ("typical-2k", lambda: (_TEXTS["typical"],)),
        ("large-mixed-25k", lambda: (_TEXTS["large-mixed"],)),
        ("mostly-misses-15k", lambda: (_TEXTS["mostly-misses"],)),
        ("long-lines-3k", lambda: (_TEXTS["long-lines"],)),
        ("no-trailing-15k", lambda: (_TEXTS["no-trailing"],)),
        ("unicode-8k", lambda: (_TEXTS["unicode"],)),
        ("duplicates-10k", lambda: (_TEXTS["duplicates"],)),
        ("near-miss-12k", lambda: (_TEXTS["near-miss"],)),
    ]
```

Wait — the thunk returns a tuple of positional args, so `(_TEXTS["typical"],)` is `(text,)` → `_parse_members(text)`. Correct.

Now, is the module-level build time acceptable? Let's estimate: total lines ~ 2000+25000+15000+3000+15000+8000+10000+12000 = 90000 lines. Each line built with several rng calls and string formatting. Maybe 0.3-1s. Fine.

Memory: total text size: large-mixed 25000 lines * ~90 chars = 2.25MB; long-lines 3000 * ~400 = 1.2MB; others ~1-1.5MB each. Total maybe 10MB. Fine.

Output sizes: large-mixed 25000 matches → 25000 dicts. Values ~75000. OK.

Now let's double-check the regex behavior for entries with trailing text: `- [Alice Smith](https://github.com/alice), maintainer since 2019` — the `(.+)` captures "maintainer since 2019". Line stored in output is `m.group(0)` = full match = the whole line. Good.

One more consideration: the harness compares outputs in full after every input. For large-mixed, output is 25000 dicts — comparison fine.

Now, potential issue: `re.compile` inside the function each call — that's part of the work, fine.

Let me also double check the "mostly-misses" case: 1% matches of 15000 = 150 matches. Good.

Now, is there any risk that a case takes > 1s? large-mixed with 2.25MB text: regex finditer. Python's re on 2MB with this pattern... The pattern starts with `^[-*+]`. In CPython's re, the engine scans for a match starting at each position. For each position, it evaluates the `^` assertion (in MULTILINE, checks if at start or preceded by newline) then the char class. This is C code, roughly 50-200 MB/s. So 2.25MB → ~10-50ms. Fine.

Hmm, but wait: is it possible that the regex is much slower due to backtracking? The pattern is mostly deterministic: `\[([^\]]+)\]\(https://github\.com/([^)]+)\)` — `[^\]]+` is greedy but with a following `\]` literal, it's linear. Then `https://github.com/` literal — this is checked at each position where `[` matched... Actually after `^[-*+] \[`, the `([^\]]+)` consumes until `]`, then requires `](https://github.com/`. If the text after `]` isn't `](https://github.com/`, it fails quickly. For near-miss lines like `- [Name](http://github.com/user)`, after `](` it checks `https://github.com/` against `http://github...` — fails at 'h' vs 's'... wait `http` vs `https`: h-t-t-p match, then 's' vs ':' mismatch. Quick fail. Good.

For lines like `- [Name](https://gitlab.com/user)`: `https://g` matches, then `i` vs `i`? "github.com/" vs "gitlab.com/" — g-i-t match, then 'h' vs 'l' mismatch. Quick.

OK.

One more: the `(.+)` at the end with `$` — greedy `.+` then backtrack to find `$`? `.+` matches to end of line (since `.` doesn't match newline), then `$` matches. Fine, linear.

Now, let's consider whether `\s*` could cause backtracking issues: `,\s*(.+)` — `\s*` greedy then `.+`. If line is `,   ` (comma + spaces only), `\s*` consumes spaces, `.+` needs ≥1 → fail; backtrack `\s*` to fewer spaces, `.+` matches a space... wait `.` matches space, so `.+` could match a space! Then `$` must match after. Hmm: line `- [Name](https://github.com/user),   ` (comma then 3 spaces). `,\s*(.+)`: `\s*` greedy takes 3 spaces, `.+` needs ≥1 char → at end, fail. Backtrack: `\s*` takes 2 spaces, `.+` takes 1 space, then `$` matches end of line. So it MATCHES with group(3) = " ". Interesting! So trailing whitespace after comma still matches. Good to know — my "near-miss" `- [Name](https://github.com/user), ` (comma + one space) would actually match! Let me re-check: line = `- [Name](https://github.com/user), ` — after `)`, we have `,` and a space, then newline. Optional group: `,` matches, `\s*` — greedy takes the space, `.+` needs ≥1 → fail; backtrack `\s*` takes 0, `.+` takes the space, `$` matches. So it MATCHES. Oops.

So that's not a miss. Let me remove that from near-miss or treat it as a match. Actually it's a fine near-miss that turns out to match — but for the case design it doesn't matter much; the case just needs diverse work. But I claimed "near-miss". Let's just replace it with a genuine miss: `- [Name](https://github.com/user),` (comma, no space, nothing after). That one: `,` matches, `\s*` empty, `.+` needs ≥1 → fail; backtrack no; optional group skipped; `$` after `)` — next char is `,` → fail. Miss. Good.

Similarly `- [Name](https://github.com/user) ` (trailing space, no comma): optional group needs `,` → skipped; `$` after `)` — next is space, not end → fail. Miss. Good.

Let me also double check `- [Name](https://github.com/user),` in mostly-misses: yes miss.

OK, let me fix the near-miss list: replace the `, ` variant with `,` variant.

Also in mostly-misses I have `f"- [{name}](https://github.com/{user}),"` — miss. Good.

Now, another thought: should I include a case where the section text is exactly what the repo passes (a section from README)? We can't fetch the real README (no network). Our synthetic is fine.

Let's also double-check the `_desc` with words like "2019" — fine.

Now, `_username` uses rng.choice over a string — returns a char. Fine.

Edge: `_username` could produce something like "---" → strip("-") → "" → "user". Fine.

Now checks():

```python
def checks():
    return [
        ("empty-text", lambda: ("",)),
        ("no-members", lambda: ("# Title\n\nJust prose, no member links here.\n",)),
        ("none-text", lambda: (None,)),
    ]
```

`None` will raise TypeError in re.finditer. That's allowed for checks. But hmm — "checked only for identical behaviour, never measured. These may raise." Both original and modified will raise the same TypeError. Fine.

Actually, is it safer to avoid None? The harness compares behaviour including exceptions presumably. It's fine. But maybe use a bytes input instead? `b"- [A](https://github.com/a)"` — re.finditer with a str pattern on bytes raises TypeError. Same thing. I'll keep None.

Hmm, one concern: if the harness renders the arguments and None is fine.

Let's finalize.

Also, should the thunks return a fresh copy? The function doesn't mutate the string. So returning the same string is fine.

One more consideration on the instruction: "Each case should make the function do substantial and different work: different paths through its code, sizes, data distributions, hit and miss ratios, duplicates, lengths." Our cases cover that.

Let me also verify that the module-level text building doesn't accidentally reference WORKDIR — not needed.

Final code:

```python
import importlib
import random

_parse_members = importlib.import_module('move-to-emeritus')._parse_members

...
```

Wait, one thing: the task says "Import the repository's modules exactly as shown in the task. Use only the standard library, the repository itself and packages the repository already imports." The given import line is `_parse_members = importlib.import_module('move-to-emeritus')._parse_members`. So we need `import importlib` too. Good.

Let me write it all out.

Also, should I worry that importing the module might fail because of `urllib` etc.? All stdlib. Fine.

Let me count the total output values for large-mixed: 25000 dicts × 3 = 75000 < 100000. OK. But also the "line" strings are long-ish. Fine.

Hmm, actually maybe reduce large-mixed to 22000 to be safer. Eh, 25000 is fine.

Let me reconsider the time budget for the original: cases should take 1ms-200ms. The typical-2k case: 2000 lines ~ 180KB → maybe 1-3ms. Might be borderline under 1ms? Let's make it 3000 lines. Actually 180KB scanning at ~100MB/s = 1.8ms. Plus building 2000 dicts. Probably ~2-4ms. OK, above 1ms. But to be safe, make typical 4000 lines.

Hmm, but "typical" should reflect reality — the real README section has maybe 100-500 members. But we need ≥1ms. Let's keep 4000; it's still "typical-ish" in structure.

Actually the requirement is "One call should take roughly 1 ms to 200 ms on the original." So all cases should be ≥ ~1ms. The smallest case must be ≥1ms. Let's ensure all cases are ≥ a few ms. typical-4k: 4000 lines × 90 chars = 360KB → ~3-5ms. Fine.

Let me set:
- typical: 4000 entries
- large-mixed: 25000
- mostly-misses: 15000 lines
- long-lines: 3000
- no-trailing: 15000
- unicode: 8000
- duplicates: 10000
- near-miss: 12000

Outputs: typical 4000, large 25000, mostly ~150, long 3000, no-trailing 15000, unicode 8000, duplicates 10000, near-miss ~5400. All fine.

Now write final answer.

One more check on `_build_mostly_misses`: the `r < 0.01` branch uses `_entry` which may or may not have trailing — fine.

Also note: in mostly-misses, `f"- [{name}](https://github.com/{user}) "` (trailing space) — miss. Good.

Let me write out the code neatly.

Also, I should double check: does `re.finditer` with a `str` pattern and `str` text work with the `^`/`$` MULTILINE — yes.

Final.