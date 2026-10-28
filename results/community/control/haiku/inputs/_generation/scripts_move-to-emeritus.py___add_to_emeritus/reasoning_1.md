We need write Python source with checks and cases. Need import module as specified: `_add_to_emeritus = importlib.import_module('move-to-emeritus')._add_to_emeritus`. But module name has hyphen; importlib.import_module works if file on path? We should do exactly. Need maybe sys.path? Repository likely scripts dir on path? The task says import exactly as shown. We can write `import importlib; _add_to_emeritus = importlib.import_module('move-to-emeritus')._add_to_emeritus`. But if scripts not on sys.path, may fail. We can add scripts path? We don't know WORKDIR. The repository is community; scripts/move-to-emeritus.py. The importlib.import_module('move-to-emeritus') requires scripts directory in sys.path. Maybe test harness sets it up. We can do `import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))`? But our source file location unknown. Better: use importlib to import from path? Instruction says import exactly as shown. Could use `import importlib; _add_to_emeritus = importlib.import_module('move-to-emeritus')._add_to_emeritus`. But to be safe, we can attempt to add likely path: repository root? We don't know. Usually these tasks run in repo root, and scripts folder not in sys.path. The instruction "Import it as ..." probably means the harness has set sys.path or module available. We'll follow exactly, maybe with fallback. But no need.

Need generate realistic README strings. Function operates on README string, finds section by title. We need cases: 8 measured inputs. Need varied: existing section with many members, no members, user already present, different header levels, section missing with "Learn more about roles" marker, missing with Licenses marker, missing with neither, various list markers, case-insensitive title, duplicates, sorting. We need ensure each call ~1ms-200ms. README size maybe 10k-100k chars, member lines hundreds. Function does regex and sorting. 200ms maybe with 10k lines. Keep under 100k values output? Output is string. Input values under 1M. Fine.

Need construct README with sections. Need understand _find_section: pattern `^(#{2,3})\s+{section_name}\s*$` MULTILINE IGNORECASE. End at next header at same or higher level: `^#{1,header_level}(?!#)\s` (so # to ###). So section ends at next header of level <= header_level. We'll build readme with emeritus section and other sections.

We need member_entry strings like `- [Name](https://github.com/username)` perhaps. _to_emeritus_entry likely produces `- [Display Name](https://github.com/username)`. We can craft.

Need cases that exercise:
1. Existing section with many members, add new member sorting, header level 3. Use 500 members.
2. Existing section with many members, add duplicate (returns unchanged) — but then work less; still measured? It returns early, maybe not most work. We need 8, harness keeps 4 most work. We can include duplicate as one but likely dropped. Better include varied heavy.
3. Existing section with no members yet (only header + blank lines), insert after header.
4. Section missing, insert before "Learn more about roles" marker.
5. Section missing, insert before "## Licenses".
6. Section missing, insert before "## License".
7. Section missing, no marker, append.
8. Existing section with different list markers (* and +) and non-member lines, trailing content, header level 2.
9. Existing section with case-insensitive title.
10. Large section with many members and trailing content, header level 3.

Need exactly 8 cases. We can pick heavy ones. Ensure no errors. Need maybe section title constant? The function takes emeritus_title. In repo, EMERITUS_SECTION likely "Emeritus Maintainers" etc. We can use "Emeritus" or "Emeritus Maintainers". We'll use "Emeritus Maintainers". The function's _find_section uses re.escape. Good.

Need checks: 2-3 small edge inputs. E.g. empty readme, section missing, no markers -> appends. One with existing section empty. One with member_entry odd? Maybe None? But function expects string; could raise. Checks may raise. But we want identical behavior; original and modified both. We can include empty string readme, and section with empty member_entry? Might not raise. Keep simple: empty readme, readme with section but no members, readme with section and duplicate? For checks small.

Need generate data at module level. Use random.Random(0). Build readme strings. Need ensure each thunk returns arguments tuple. For function `_add_to_emeritus(readme, emeritus_title, member_entry, header_level=3)`. So thunk returns `(readme, title, entry, header_level)` or `call(...)`. We can use positional tuple. For default header level, we can omit? Thunk returns args tuple; if we want default, return `(readme, title, entry)`.

Need be careful: function may modify readme? It returns new string, doesn't mutate. So can reuse same readme across calls. But if function has no side effects, fine. However, if we call many times, same input. That's okay. But for duplicate case, returns readme. For cases where section exists and we add member, the entry is same each call; if it adds same entry, then after first call the readme passed is original (not modified), so each call same. Good.

Need build realistic README. Let's design helper functions.

We need a base README with various sections. For existing section, we can build:

```
# Community

Some intro.

## Maintainers

- [Alice](https://github.com/alice)
...

## Emeritus Maintainers

- [Bob](https://github.com/bob)
- [Carol](https://github.com/carol)
...

## Approvers

...
```

But _find_section for "Emeritus Maintainers" with header level 3? If header is `### Emeritus Maintainers`, end at next header of level <=3. If following `## Approvers`, that's level 2, so end before. Good. If header level 2, end at next level <=2 (##). So we can set.

Need create many member lines. Use random names to avoid sorted pattern? The function sorts, so input order doesn't matter much. But to stress sorting, random order. Use names with varied case, numbers, punctuation? Display names inside brackets. Usernames unique. Include non-member lines within section (e.g. blank lines, explanatory text) to test separation. The function separates member lines by regex `^[-*+] \[` and then appends new entry, sorts, and rebuilds: it keeps non-member lines before first member and after last member. So non-member lines inside between members get dropped? Actually it takes lines[:first_member_idx] + member_lines + lines[last_member_idx+1:], so any non-member lines between first and last member are removed. That's part of behavior. We can include some.

Need ensure section_text includes header line and content. _find_section start at header match start, end at next header start. So section_text includes header and all lines until before next header. Good.

For missing section cases: build readme with markers. Need ensure _find_section returns None. Then new_section inserted. For "Learn more about roles" marker: `idx = readme.find("\nLearn more about roles")`; then `return readme[:idx] + new_section + "\n" + readme[idx + 1 :]`. So marker line. We'll include.

For Licenses: `\n## Licenses` or `\n## License`. Insert before. Good.

For no marker: append.

Need make each case heavy enough. Let's estimate. Sorting 1000 lines with regex per line is maybe ~1ms. To get 1-200ms, use 5000-20000 member lines. Regex on 20k lines maybe 20ms. Good. But output string size ~1MB? 20k lines * 50 chars = 1MB, under 100MB. Input values under 1M? "keep each input's data under about 1 000 000 values" — string length maybe 1M chars, okay. Output string similar. Keep under 100k values? Output is string, maybe they count length? "keep what it returns under about 100 000 values" — for string, length? Might be interpreted as values. A 1MB string might be too large? They said under 100,000 values, but for strings maybe characters? To be safe, use ~5000-10000 lines, ~500KB. The function's output is string. 100k values could be lines? We'll keep lines under ~10k. 10k lines * 50 = 500k chars. Fine.

Need 8 cases with different sizes and paths. Let's define helper `_make_readme(n_members, header_level=3, marker=None, include_section=True, list_marker='-', extra_trailing=True, seed=0)`. But we need different structures. We can write explicit builders.

Let's plan cases:

1. `existing-large`: README with `### Emeritus Maintainers` section containing 8000 member lines randomly ordered, plus some non-member lines, followed by `## Approvers` section. Add new member. header_level=3. This is heavy sorting.
2. `existing-empty`: Section exists with header and blank lines, no members. Add member. Less heavy but tests insert path. To make it heavier, include many other sections? But function only processes section text; if no members, it does little. Could still be measured but likely dropped. Need 8 total, keep 4 most work. We can include some heavy ones.
3. `existing-level2`: Header `## Emeritus Maintainers` with 6000 members, followed by `### Subsection`? Wait end at next header of level <=2. If next is `###`, level 3 >2, so section continues. We can include trailing content with `###` subheader to test end detection. Add member. header_level=2. Heavy.
4. `missing-learn-more`: No emeritus section, README has `\nLearn more about roles` marker. Add member. header_level=3. The function creates section and inserts. Work is small (find section fails, find marker, string concat). To make it heavier, make README large with many sections before marker. But function only does string find and concat. Still maybe 1ms if README large. We can make README 500KB. But sorting not done. Could be less work. Harness keeps 4 most work, so these may be dropped. We need at least 4 heavy sorting cases. So we can have 4 heavy existing-section cases and 4 missing/empty cases. That's fine.
5. `missing-licenses`: No section, has `\n## Licenses`. Large README.
6. `missing-license`: No section, has `\n## License`. Large README.
7. `missing-none`: No section, no markers. Append. Large README.
8. `duplicate`: Existing section with many members, member_entry username already present. Returns early. Heavy? It does _find_section, then regex search on section_text. If section_text large, regex search is fast. Less work. Could be dropped. But we need 8. Maybe replace with another heavy existing case: e.g. existing section with many members and list markers `*` and `+`, header level 3, add new member. That's heavy. And include duplicate as one? We need 8 exactly. Let's choose 5 heavy existing cases + 3 missing cases. That gives 4 heavy kept. Good.

Let's define cases:
1. existing-large (8000 members, `-`, level 3, random order, some non-member lines, trailing `## Approvers`)
2. existing-level2 (6000 members, `-`, level 2, trailing `### Notes` and `## License`? Wait end at next header level <=2. If trailing `### Notes` level 3, section continues; then `## License` level 2 ends. So section includes `### Notes` and its content. Good. Add member. Header level 2. This tests end pattern with `###` not ending. Heavy.
3. existing-mixed-markers (7000 members, mix `-`, `*`, `+`, level 3, non-member lines, trailing `## Other`)
4. existing-case-insensitive (5000 members, title "emeritus maintainers" lower case in readme, but pass "Emeritus Maintainers", level 3)
5. existing-duplicate (8000 members, add entry with existing username) — returns early, less work. Could be dropped. But okay.
6. missing-learn-more (large README with marker)
7. missing-licenses (large README with `## Licenses`)
8. missing-none (large README no markers)

But we need exactly 8 measured inputs. The harness keeps 4 that do most work. So heavy ones 1-4 likely kept. Good.

Need ensure checks() 2-3 small edge inputs. We'll do:
- empty readme, missing section, no markers -> appends.
- readme with section header only, no members -> inserts.
- readme with section and member_entry None? Might raise TypeError. But checks may raise. However, if original raises, modified must raise same? They compare behavior maybe exceptions. But safer to avoid None. Use empty member_entry string? `_add_to_emeritus("### Emeritus\n\n", "Emeritus", "")` might work. But empty member_entry: username_match None, member_lines append "", sort, etc. Could be odd but runs. Use small.

Need import module. We'll write:

```python
import importlib
import random
import re

_mod = importlib.import_module('move-to-emeritus')
_add_to_emeritus = _mod._add_to_emeritus
```

But if module not found, maybe need add scripts to sys.path. We can do:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
```

But `__file__` may not be defined? In these tasks, source is executed as a module? Usually yes. But to be safe, we can try import and on failure add 'scripts'. However, instruction says import exactly as shown. We can just use importlib.import_module. The test harness likely sets cwd to repo root and adds scripts? Actually `importlib.import_module('move-to-emeritus')` will search sys.path. The scripts directory is not normally on sys.path. But the task explicitly says "Import it as `_add_to_emeritus = importlib.import_module('move-to-emeritus')._add_to_emeritus`". They likely have a custom import hook or set sys.path. We'll follow. Maybe also add fallback:

```python
try:
    _mod = importlib.import_module('move-to-emeritus')
except ModuleNotFoundError:
    import pathlib
    # try scripts relative to cwd
    sys.path.insert(0, str(pathlib.Path.cwd() / 'scripts'))
    _mod = importlib.import_module('move-to-emeritus')
```

But using cwd may be wrong. However, it's safe. But instruction says import exactly as shown; adding fallback might be okay. But we should not overcomplicate. We'll just use the exact line.

Need build README. Let's write helper functions.

```python
def _member_line(name, username, marker='-'):
    return f"{marker} [{name}](https://github.com/{username})"
```

Generate names: use random.Random(seed). Use list of first names, last names? To ensure sorting varied, generate random strings. Use `f"Person{i:05d} {rng.choice(['Alpha','beta','Gamma'])}"` etc. But display names inside brackets. Need usernames unique. For duplicate case, we need know a username. We can generate and pick one.

We need build README with sections. Let's define:

```python
def _make_readme_with_section(n_members, header_level=3, title="Emeritus Maintainers", marker='-', seed=0, mixed=False, extra_lines=True):
    rng = random.Random(seed)
    lines = []
    lines.append("# Community")
    lines.append("")
    lines.append("Intro text.")
    lines.append("")
    # Add some other sections before
    lines.append("## Maintainers")
    lines.append("")
    for i in range(50):
        lines.append(_member_line(f"Maint {i}", f"maint{i}", '-'))
    lines.append("")
    hashes = "#" * header_level
    lines.append(f"{hashes} {title}")
    lines.append("")
    # Generate members
    members = []
    for i in range(n_members):
        m = marker
        if mixed:
            m = rng.choice(['-', '*', '+'])
        name = f"Person {rng.randrange(100000):05d} {rng.choice(['Alpha','beta','Gamma','delta'])}"
        username = f"user{i}_{rng.randrange(10000)}"
        members.append(_member_line(name, username, m))
    rng.shuffle(members)
    # Insert some non-member lines
    if extra_lines and n_members > 10:
        members.insert(5, "Some explanatory text.")
        members.insert(n_members//2, "")
        members.insert(n_members-5, "Another note.")
    lines.extend(members)
    lines.append("")
    # Trailing content
    if header_level == 3:
        lines.append("### Notes")
        lines.append("Some notes about emeritus.")
        lines.append("")
    lines.append("## Approvers")
    lines.append("")
    for i in range(20):
        lines.append(_member_line(f"App {i}", f"app{i}", '-'))
    lines.append("")
    lines.append("## Licenses")
    lines.append("")
    lines.append("License text.")
    return "\n".join(lines)
```

But for header_level=2, the section end pattern looks for next header of level <=2. `### Notes` is level 3, so not end. Then `## Approvers` is level 2, so end. Good. For header_level=3, `### Notes` is level 3, which is <=3, so it ends at `### Notes`. So section_text won't include Notes. That's fine. We can adjust: for level 3, don't include `### Notes`; or include but it ends section. That's okay. For level 2, include `### Notes` to test not ending. Good.

Need ensure _find_section matches title exactly with optional whitespace. Our title line `### Emeritus Maintainers` matches. If title case-insensitive, we can pass title lower in readme. Good.

For missing section READMEs, build large README without emeritus section. Use helper `_make_readme_no_section(n_sections, marker_type, seed)`. We can create many sections with members to make it large. For missing-learn-more, include `\nLearn more about roles` line. For missing-licenses, include `\n## Licenses`. For missing-license, `\n## License`. For missing-none, no markers. Need ensure no accidental "Emeritus Maintainers" header. Use other titles.

Let's write:

```python
def _make_readme_no_emeritus(n_sections=200, marker=None, seed=0):
    rng = random.Random(seed)
    lines = ["# Community", ""]
    for s in range(n_sections):
        lines.append(f"## Section {s}")
        lines.append("")
        for i in range(20):
            lines.append(_member_line(f"Name {s}-{i}", f"user{s}_{i}", '-'))
        lines.append("")
    if marker == "learn":
        lines.append("Learn more about roles")
        lines.append("")
    elif marker == "licenses":
        lines.append("## Licenses")
        lines.append("")
        lines.append("License text.")
        lines.append("")
    elif marker == "license":
        lines.append("## License")
        lines.append("")
        lines.append("License text.")
        lines.append("")
    # add trailing
    lines.append("## Footer")
    lines.append("")
    lines.append("Footer text.")
    return "\n".join(lines)
```

But for missing-learn-more, the function looks for `\nLearn more about roles`. Our line is preceded by newline? The previous line is "" so there is `\n\nLearn more...`? Actually lines joined with `\n`. If we append "Learn more about roles" after a blank line, the string has `\n\nLearn more...`; the find `\nLearn more` will find the second newline before Learn? Yes, `\nLearn` occurs at the newline immediately before "Learn", which is the second newline. So idx points to that newline. Good.

For missing-licenses, function looks for `\n## Licenses`. Our line `## Licenses` preceded by blank line gives `\n\n## Licenses`, find `\n## Licenses` finds the second newline. Good.

Need make README large enough. n_sections=200, each section ~20 members * 50 = 1000 chars, total 200k chars. Fine.

Now cases. Need thunks return arguments. For existing cases, readme built once at module level. We can build in module-level variables. But building all 8 READMEs at import may take time but under 10s. 8000 members * 5 = 40k lines, fine. We can build lazily in thunks? Instruction says build large data once at module level. We'll build at module level.

Let's define variables:

```python
_README_LARGE = _make_readme_with_section(8000, header_level=3, seed=1)
_README_LEVEL2 = _make_readme_with_section(6000, header_level=2, seed=2, extra_lines=True)
_README_MIXED = _make_readme_with_section(7000, header_level=3, seed=3, mixed=True)
_README_CASE = _make_readme_with_section(5000, header_level=3, title="emeritus maintainers", seed=4)
_README_DUP = _make_readme_with_section(8000, header_level=3, seed=5)
```

But for duplicate, need entry with a username that exists in section. We can pick a known username. Our generator uses usernames `user{i}_{rng.randrange(10000)}` but we don't know which. We can modify generator to return readme and list of usernames? Or for duplicate, we can just use a fixed username and ensure it's in the readme. We can create a readme with a known member line. Easier: after building `_README_DUP`, we know we can pick a username from the generated members? But the generator doesn't return. We can create a specific duplicate case with a small known section and many other members. Or we can just use `member_entry = "- [Duplicate](https://github.com/duplicate_user)"` and ensure the readme contains `https://github.com/duplicate_user` in section. We can add that line manually to the readme. Let's write a helper to build duplicate readme with one known member plus many random. Or we can use `_README_LARGE` and pick a username from it? Not easily. We'll create a separate builder:

```python
def _make_readme_duplicate(n_members, seed=6):
    rng = random.Random(seed)
    lines = ["# Community", "", "## Maintainers", ""]
    # ... 
    lines.append("### Emeritus Maintainers")
    lines.append("")
    lines.append("- [Known User](https://github.com/known_user)")
    for i in range(n_members):
        ...
    lines.append("")
    lines.append("## Approvers")
    ...
```

Then member_entry = "- [Known User](https://github.com/known_user)". The function will find username `known_user` and return readme unchanged. This case does less work but still _find_section and regex search. We can include as one of 8.

But we need 8 cases. Let's list:

1. "existing-large" -> `_README_LARGE`, title "Emeritus Maintainers", entry new, header_level 3.
2. "existing-level2" -> `_README_LEVEL2`, title, entry new, header_level 2.
3. "existing-mixed-markers" -> `_README_MIXED`, title, entry new, header_level 3.
4. "existing-case-insensitive" -> `_README_CASE`, title "Emeritus Maintainers", entry new, header_level 3.
5. "existing-duplicate" -> `_README_DUP`, title, entry known, header_level 3.
6. "missing-learn-more" -> `_README_NO_LEARN`, title, entry new, header_level 3.
7. "missing-licenses" -> `_README_NO_LICENSES`, title, entry new, header_level 3.
8. "missing-none" -> `_README_NO_NONE`, title, entry new, header_level 3.

But we need maybe a case with existing section but no members. Could be checks. We have checks for that.

Need ensure each case runs without raising. For existing cases, member_entry must be a string. For missing, same.

Let's write generator for existing with known duplicate. We can modify `_make_readme_with_section` to accept `known_member` parameter. Or just create `_README_DUP` by building a readme with a known member inserted. Let's write a separate function:

```python
def _make_readme_duplicate(n_members=8000, seed=6):
    rng = random.Random(seed)
    lines = ["# Community", "", "## Maintainers", ""]
    for i in range(100):
        lines.append(_member_line(f"Maint {i}", f"maint{i}", '-'))
    lines.append("")
    lines.append("### Emeritus Maintainers")
    lines.append("")
    lines.append("- [Known User](https://github.com/known_user)")
    for i in range(n_members):
        name = f"Person {rng.randrange(100000):05d}"
        username = f"user{i}_{rng.randrange(10000)}"
        lines.append(_member_line(name, username, '-'))
    lines.append("")
    lines.append("## Approvers")
    lines.append("")
    for i in range(50):
        lines.append(_member_line(f"App {i}", f"app{i}", '-'))
    lines.append("")
    lines.append("## Licenses")
    lines.append("")
    lines.append("License text.")
    return "\n".join(lines)
```

Good.

Need check `_find_section` matches `### Emeritus Maintainers` and end at `## Approvers` because header_level=3, end pattern `^#{1,3}(?!#)\s` matches `## Approvers`? Wait `^#{1,3}(?!#)\s` means 1 to 3 hashes not followed by another hash, then whitespace. `## Approvers` has two hashes, next char is space, so matches. Yes, end at `## Approvers`. Good.

For level2 readme, our generator `_make_readme_with_section` with header_level=2 adds `### Notes` after members. Since header_level=2, end pattern `^#{1,2}(?!#)\s` will not match `### Notes` because after two hashes, next char is `#` (negative lookahead fails). It will match `## Approvers`. So section includes `### Notes`. That's fine.

Need ensure title line for level2 is `## Emeritus Maintainers`. _find_section pattern `^(#{2,3})\s+...` matches. header_level=2. Good.

Now, potential issue: `_add_to_emeritus` uses `re` module imported in the module. Our code uses `re`? Not needed.

Need write checks. For checks, small readmes:

```python
def checks():
    return [
        ("empty-readme", lambda: ("", "Emeritus Maintainers", "- [New](https://github.com/new)")),
        ("section-no-members", lambda: ("# Community\n\n### Emeritus Maintainers\n\n## Approvers\n", "Emeritus Maintainers", "- [New](https://github.com/new)")),
        ("odd-entry", lambda: ("# Community\n\n### Emeritus Maintainers\n\n- [Old](https://github.com/old)\n", "Emeritus Maintainers", "")),
    ]
```

Third with empty member_entry might cause issues? Let's trace: section exists, section_text = "### Emeritus Maintainers\n\n- [Old](https://github.com/old)\n". username_match on empty member_entry: re.search returns None, so no early return. lines = section_text.split("\n") -> ["### Emeritus Maintainers", "", "- [Old](https://github.com/old)", ""]. member_lines = ["- [Old](https://github.com/old)"], append "" -> ["- [Old](https://github.com/old)", ""]. Sort: _sort_key on "" -> m = re.match(...) returns None, returns line.lower() -> "". So sorted: "" first? Actually "" < "- [Old]..." so member_lines becomes ["", "- [Old]..."]. Then first_member_idx = 2, last_member_idx = 2. new_lines = lines[:2] + ["", "- [Old]..."] + lines[3:] -> ["### Emeritus Maintainers", "", "", "- [Old]...", ""]. new_section = "\n".join(...). Returns readme[:start] + new_section + readme[end:]. Should run. But maybe weird. It's fine. But to avoid potential exceptions, use a normal small entry. We can use "odd-type" with header_level=4? The function default header_level=3, but if we pass header_level=1? It will create `#` section. But _find_section only matches 2-3 hashes, so if section missing, header_level=1 creates `# Emeritus`. That's valid. But checks may raise? No. We can do "header-level-1" with missing section. But not needed.

Let's keep checks simple and safe:
- empty readme
- readme with section no members
- readme with section and duplicate entry (returns unchanged)

Third: `("# Community\n\n### Emeritus Maintainers\n\n- [Old](https://github.com/old)\n\n## Approvers\n", "Emeritus Maintainers", "- [Old](https://github.com/old)")` -> duplicate returns readme. Runs.

Need ensure thunks for cases return tuple. For header_level default, we can return 3 args or 4. We'll return 4 to be explicit. For duplicate, same.

Now, module-level building all READMEs. Need avoid too much memory. 8000 members * 5 readmes ~ 40k lines, ~2MB. Fine.

Let's write code carefully.

Potential issue: `importlib.import_module('move-to-emeritus')` may fail if module not on path. We can add a fallback to insert `scripts` directory. Since the repository is community, the script is at `scripts/move-to-emeritus.py`. The test harness likely runs from repo root. We can do:

```python
import importlib
import os
import sys

try:
    _mod = importlib.import_module('move-to-emeritus')
except ModuleNotFoundError:
    _scripts = os.path.join(os.getcwd(), 'scripts')
    if os.path.isdir(_scripts):
        sys.path.insert(0, _scripts)
    _mod = importlib.import_module('move-to-emeritus')
_add_to_emeritus = _mod._add_to_emeritus
```

But instruction says "Import it as `_add_to_emeritus = importlib.import_module('move-to-emeritus')._add_to_emeritus`". Our fallback still does that. It's fine. However, if `__file__` is available, we could use `os.path.dirname(__file__)`. But cwd is likely repo root. We'll include fallback.

Need not import `call` unless using keyword args. We use positional tuples, so no `call`.

Let's write the full source.

Check the function signature: `_add_to_emeritus(readme, emeritus_title, member_entry, header_level=3)`. Our thunks return 4-tuple. Good.

Now, let's think about whether the function might be called many times and mutate something. It only uses local variables and regex. No global mutation except maybe re cache. Fine.

One more thing: The harness compares outputs in full. Our readmes are large; output string comparison might be heavy but okay.

Let's ensure the generated readmes don't contain accidental "Emeritus Maintainers" in other sections. Our `_make_readme_no_emeritus` uses "Section {s}", so no. Good.

For `_make_readme_with_section`, title is "Emeritus Maintainers" or lower. Only one occurrence. Good.

For duplicate, known_user appears once. The regex search in section_text uses `https://github\.com/known_user[)/]`. Our line has `https://github.com/known_user)` so matches. Returns readme unchanged.

Now, need ensure `_find_section` for missing cases returns None. Our no-emeritus readmes don't have "Emeritus Maintainers" header. Good.

Let's write code.

Potential issue: `_make_readme_with_section` for level2 includes `### Notes` after members. But the section end pattern for header_level=2 will not end at `### Notes`, so section_text includes `### Notes` and its content. Then when rebuilding, `lines` includes `### Notes` and "Some notes...". The function separates member lines, appends new entry, sorts. It finds first_member_idx and last_member_idx. The non-member lines before first member (header, blank) are kept, and lines after last member (blank, ### Notes, notes, blank) are kept. So it inserts sorted members before `### Notes`. That's fine. It does more work. Good.

For level3, our generator adds `### Notes` after members. But end pattern for header_level=3 will end at `### Notes` (since level 3 <=3). So section_text ends before `### Notes`. That's fine. The section_text includes only header and members and blank line. Good.

Let's ensure `_make_readme_with_section` for level3 doesn't include `### Notes` inside section. It doesn't matter.

Now, code:

```python
import importlib
import os
import random
import sys

try:
    _mod = importlib.import_module('move-to-emeritus')
except ModuleNotFoundError:
    _scripts = os.path.join(os.getcwd(), 'scripts')
    if os.path.isdir(_scripts):
        sys.path.insert(0, _scripts)
    _mod = importlib.import_module('move-to-emeritus')
_add_to_emeritus = _mod._add_to_emeritus

def _member_line(name, username, marker='-'):
    return f"{marker} [{name}](https://github.com/{username})"

def _make_readme_with_section(n_members, header_level=3, title="Emeritus Maintainers", marker='-', seed=0, mixed=False, extra_lines=True):
    rng = random.Random(seed)
    lines = ["# Community", "", "Intro text.", "", "## Maintainers", ""]
    for i in range(100):
        lines.append(_member_line(f"Maint {i}", f"maint{i}", '-'))
    lines.append("")
    hashes = "#" * header_level
    lines.append(f"{hashes} {title}")
    lines.append("")
    members = []
    for i in range(n_members):
        m = marker
        if mixed:
            m = rng.choice(['-', '*', '+'])
        name = f"Person {rng.randrange(100000):05d} {rng.choice(['Alpha','beta','Gamma','delta'])}"
        username = f"user{i}_{rng.randrange(10000)}"
        members.append(_member_line(name, username, m))
    rng.shuffle(members)
    if extra_lines and n_members > 10:
        members.insert(5, "Some explanatory text.")
        members.insert(n_members // 2, "")
        members.insert(n_members - 5, "Another note.")
    lines.extend(members)
    lines.append("")
    if header_level == 2:
        lines.append("### Notes")
        lines.append("Some notes about emeritus.")
        lines.append("")
    lines.append("## Approvers")
    lines.append("")
    for i in range(50):
        lines.append(_member_line(f"App {i}", f"app{i}", '-'))
    lines.append("")
    lines.append("## Licenses")
    lines.append("")
    lines.append("License text.")
    return "\n".join(lines)

def _make_readme_duplicate(n_members=8000, seed=6):
    rng = random.Random(seed)
    lines = ["# Community", "", "## Maintainers", ""]
    for i in range(100):
        lines.append(_member_line(f"Maint {i}", f"maint{i}", '-'))
    lines.append("")
    lines.append("### Emeritus Maintainers")
    lines.append("")
    lines.append("- [Known User](https://github.com/known_user)")
    for i in range(n_members):
        name = f"Person {rng.randrange(100000):05d} {rng.choice(['Alpha','beta','Gamma'])}"
        username = f"user{i}_{rng.randrange(10000)}"
        lines.append(_member_line(name, username, '-'))
    lines.append("")
    lines.append("## Approvers")
    lines.append("")
    for i in range(50):
        lines.append(_member_line(f"App {i}", f"app{i}", '-'))
    lines.append("")
    lines.append("## Licenses")
    lines.append("")
    lines.append("License text.")
    return "\n".join(lines)

def _make_readme_no_emeritus(n_sections=200, marker=None, seed=0):
    rng = random.Random(seed)
    lines = ["# Community", ""]
    for s in range(n_sections):
        lines.append(f"## Section {s}")
        lines.append("")
        for i in range(20):
            lines.append(_member_line(f"Name {s}-{i}", f"user{s}_{i}", '-'))
        lines.append("")
    if marker == "learn":
        lines.append("Learn more about roles")
        lines.append("")
    elif marker == "licenses":
        lines.append("## Licenses")
        lines.append("")
        lines.append("License text.")
        lines.append("")
    elif marker == "license":
        lines.append("## License")
        lines.append("")
        lines.append("License text.")
        lines.append("")
    lines.append("## Footer")
    lines.append("")
    lines.append("Footer text.")
    return "\n".join(lines)

_README_LARGE = _make_readme_with_section(8000, header_level=3, seed=1)
_README_LEVEL2 = _make_readme_with_section(6000, header_level=2, seed=2)
_README_MIXED = _make_readme_with_section(7000, header_level=3, seed=3, mixed=True)
_README_CASE = _make_readme_with_section(5000, header_level=3, title="emeritus maintainers", seed=4)
_README_DUP = _make_readme_duplicate(8000, seed=5)
_README_NO_LEARN = _make_readme_no_emeritus(200, marker="learn", seed=6)
_README_NO_LICENSES = _make_readme_no_emeritus(200, marker="licenses", seed=7)
_README_NO_NONE = _make_readme_no_emeritus(200, marker=None, seed=8)

_NEW_ENTRY = "- [New Person](https://github.com/new_person)"
_DUP_ENTRY = "- [Known User](https://github.com/known_user)"
_TITLE = "Emeritus Maintainers"

def checks():
    return [
        ("empty-readme", lambda: ("", _TITLE, _NEW_ENTRY)),
        ("section-no-members", lambda: ("# Community\n\n### Emeritus Maintainers\n\n## Approvers\n", _TITLE, _NEW_ENTRY)),
        ("duplicate-small", lambda: ("# Community\n\n### Emeritus Maintainers\n\n- [Old](https://github.com/old)\n\n## Approvers\n", _TITLE, "- [Old](https://github.com/old)")),
    ]

def cases():
    return [
        ("existing-large", lambda: (_README_LARGE, _TITLE, _NEW_ENTRY, 3)),
        ("existing-level2", lambda: (_README_LEVEL2, _TITLE, _NEW_ENTRY, 2)),
        ("existing-mixed-markers", lambda: (_README_MIXED, _TITLE, _NEW_ENTRY, 3)),
        ("existing-case-insensitive", lambda: (_README_CASE, _TITLE, _NEW_ENTRY, 3)),
        ("existing-duplicate", lambda: (_README_DUP, _TITLE, _DUP_ENTRY, 3)),
        ("missing-learn-more", lambda: (_README_NO_LEARN, _TITLE, _NEW_ENTRY, 3)),
        ("missing-licenses", lambda: (_README_NO_LICENSES, _TITLE, _NEW_ENTRY, 3)),
        ("missing-none", lambda: (_README_NO_NONE, _TITLE, _NEW_ENTRY, 3)),
    ]
```

Check: For `_README_NO_LEARN`, marker "learn" adds "Learn more about roles". But there is a preceding blank line, so string contains `\n\nLearn more about roles`. The function finds `\nLearn more about roles` at the newline before "Learn". Good. It then returns `readme[:idx] + new_section + "\n" + readme[idx + 1 :]`. So it inserts new section and a newline, then the rest starting at "Learn...". Good.

For `_README_NO_LICENSES`, marker "licenses" adds "## Licenses". Preceded by blank line, so `\n\n## Licenses`. Function finds `\n## Licenses` at the newline before `##`. Good. It inserts before.

For `_README_NO_NONE`, no marker, appends.

Potential issue: `_make_readme_no_emeritus` uses `## Section {s}`. The function `_find_section` searches for `Emeritus Maintainers`, so no match. Good.

Now, check the function's `_find_section` end pattern for existing-large: header_level=3. Section starts at `### Emeritus Maintainers`. End pattern `^#{1,3}(?!#)\s` will match `## Approvers` (two hashes, space). It will also match `### Notes` if present, but for level3 we don't add Notes. So end at `## Approvers`. Good.

For existing-level2: header_level=2. Section starts at `## Emeritus Maintainers`. End pattern `^#{1,2}(?!#)\s` will match `## Approvers` but not `### Notes` (three hashes). So section includes `### Notes` and its content. Then `## Approvers` ends. Good.

For existing-mixed: header_level=3, mixed markers. Section end at `## Approvers`. Good.

For existing-case: title in readme is "emeritus maintainers" lower case. _find_section pattern uses re.IGNORECASE, so matches. Good.

For existing-duplicate: section has known_user. member_entry has known_user. username_match extracts `known_user`. Then re.search in section_text for `https://github.com/known_user[)/]` with IGNORECASE. Our line has `https://github.com/known_user)` so matches. Returns readme unchanged. Good.

Now, performance: 8000 members sorting with regex per line. Should be maybe 20-50ms. Good.

One concern: `_add_to_emeritus` uses `re.match(r'^[-*+] \[', l)` for each line. 8000 lines. Fine.

Another concern: The harness runs each case many times. Our thunks return the same readme string. The function doesn't mutate it. Good. For duplicate, returns same. Good.

Now, checks: third check has duplicate small. It should run. The readme has section with one member. member_entry same. Returns unchanged. Good.

We need ensure no `call` used. We use tuples.

Now, final output: exactly one python block. We'll output the code.

Let's double-check import fallback: `os.getcwd()` might be repo root. If not, maybe `scripts` not found. But the task says import as shown, so likely works. Our fallback is harmless. However, if `importlib.import_module('move-to-emeritus')` raises ModuleNotFoundError, we add scripts and try again. If still fails, it raises. That's fine.

We should not import `re` in our code? We don't use it. The module imports re. Fine.

Let's consider if `_make_readme_with_section` for header_level=2 adds `### Notes` which is a header. The function's `_find_section` end pattern for header_level=2 will not match `### Notes`, so section includes it. But then when rebuilding, it separates member lines. The `### Notes` line is not a member line, so it's kept after last member. That's fine. However, the function's `_find_section` for header_level=2 might also match `### Notes` as a potential start? No, it only searches for the section title. The end pattern is separate. Good.

One more: The `_make_readme_with_section` for header_level=2 has `## Approvers` after `### Notes`. The end pattern for header_level=2 will match `## Approvers` (two hashes, space). So section ends at `## Approvers`. Good.

Now, maybe the function's `_find_section` pattern for section_name uses `\s*$` with MULTILINE. Our title line has no trailing spaces. Good.

Now, we should ensure the generated readme strings are not too large. 8000 members * ~60 chars = 480k. Plus other sections. Under 1MB. Good.

Now, final answer.