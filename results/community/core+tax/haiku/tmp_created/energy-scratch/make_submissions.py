import ast
import json
import sys

REPO = "/home/javad/energy-run/community"


def function_source(path, qualname):
    """Return the exact source text of a top-level function or method."""
    text = open(f"{REPO}/{path}", encoding="utf-8").read()
    lines = text.splitlines(keepends=True)
    tree = ast.parse(text)
    parts = qualname.split(".")
    scope = tree.body
    node = None
    for name in parts:
        node = next(n for n in scope if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == name)
        scope = node.body
    start = node.lineno - 1
    end = node.end_lineno
    return "".join(lines[start:end])


def apply(src, edits):
    for old, new in edits:
        n = src.count(old)
        assert n == 1, (n, old[:80])
        src = src.replace(old, new)
    return src


def sub(id_, root, path, qualname, edits, sole, notes):
    unit = f"{path}::{qualname}"
    original = function_source(path, qualname)
    changed_src = apply(original, edits)
    assert changed_src != original
    return {
        "id": id_,
        "root_cause": root,
        "unit": unit,
        "changed": {unit: changed_src},
        "sole_caller_evidence": sole,
        "notes": notes,
    }


subs = []

# 1. C3.S2: hoist the three membership sets out of the per-workstream loop
subs.append(sub(
    "C3S2-validate-hoist-sets", "C3.S2",
    "scripts/validate-workstreams.py", "validate_workstreams_semantics",
    [
        ('''        teams = people_data.get("teams", {})
        gc_members    = {u.lower() for u in teams.get("governance-committee", [])}
        tc_members    = {u.lower() for u in teams.get("technical-committee", [])}
        spec_sponsors = {u.lower() for u in teams.get("spec-sponsors", [])} | tc_members

''', ''),
         ('''    for w in workstreams:
        wid  = w.get("id", "(unknown)")
''', '''    teams = people_data.get("teams", {})
    gc_members    = {u.lower() for u in teams.get("governance-committee", [])}
    tc_members    = {u.lower() for u in teams.get("technical-committee", [])}
    spec_sponsors = {u.lower() for u in teams.get("spec-sponsors", [])} | tc_members

    for w in workstreams:
        wid  = w.get("id", "(unknown)")
'''),
    ],
    "validate_workstreams_semantics is called once, at scripts/validate-workstreams.py:184 in main(). A grep of the repository, excluding .claude and .energy-inputs, finds no other reference to the name.",
    "Sets are built from people_data once rather than once per workstream. Nothing mutates them.",
))

# 2. C1.S1: delete the unread parent_kind binding
subs.append(sub(
    "C1S1-validate-dead-parent-kind", "C1.S1",
    "scripts/validate-workstreams.py", "validate_workstreams_semantics",
    [
        ('''        parent_kind = id_to_workstream[parent_id].get("kind", "")
''', ''),
    ],
    "validate_workstreams_semantics is called once, at scripts/validate-workstreams.py:184 in main(). A grep of the repository finds no other reference, and parent_kind is a local that nothing reads.",
    "Removes the dead lookup at the line the step-1 record cites as 103.",
))

# 3. C10.S4: collect the SIG rows and join once
subs.append(sub(
    "C10S4-render-group-join", "C10.S4",
    "scripts/update-sig-tables.py", "render_group",
    [
        ('''    for ws in sigs:
        name = ws["name"]
        data = extract_row_data(ws)
        details = f"[Details](./{sigs_file}#{heading_anchor(name)})"
        content += f"| {name} | {data['meeting_schedule']} | {data['calendar']} | {join_details(data['slack_channels'])} | {details} |\\n"

    content += "\\n"
''', '''    rows = []
    for ws in sigs:
        name = ws["name"]
        data = extract_row_data(ws)
        details = f"[Details](./{sigs_file}#{heading_anchor(name)})"
        rows.append(f"| {name} | {data['meeting_schedule']} | {data['calendar']} | {join_details(data['slack_channels'])} | {details} |\\n")

    content += "".join(rows)
    content += "\\n"
'''),
    ],
    "render_group is called only at scripts/update-sig-tables.py:209-212, at module level. A grep finds no other reference.",
    "The step-1 record cites lines 372 and 374 for this unit, from a listing that ran several files together. The lines in update-sig-tables.py are 157 and 159. The edit is the same either way.",
))

# 4. C1.S4: compute each comment's mentions once and reuse them in both loops
subs.append(sub(
    "C1S4-sync-mentions-once", "C1.S4",
    "scripts/gc-elections/create-github-comments.py", "sync",
    [
        ('''    tagged_lower = set()
    for c in voter_comments:
        for m in extract_mentions(c.get('body') or ''):
            tagged_lower.add(m.lower())
''', '''    tagged_lower = set()
    mentions_of = [extract_mentions(c.get('body') or '') for c in voter_comments]
    for comment_mentions in mentions_of:
        for m in comment_mentions:
            tagged_lower.add(m.lower())
'''),
        ('''    for c in voter_comments:
        original = c.get('body') or ''
        new_body = original
        removed = []
        for m in extract_mentions(original):
''', '''    for c, comment_mentions in zip(voter_comments, mentions_of):
        original = c.get('body') or ''
        new_body = original
        removed = []
        for m in comment_mentions:
'''),
    ],
    "sync is called only at scripts/gc-elections/create-github-comments.py:220 in main(). A grep finds no other reference.",
    "The step-1 record cites lines 332 and 341 for this unit, from a listing that ran several files together. The lines in create-github-comments.py are 136 and 145.",
))

# 5. C10.S2: startswith on a fixed three-character prefix instead of re.match
subs.append(sub(
    "C10S2-add-emeritus-startswith", "C10.S2",
    "scripts/move-to-emeritus.py", "_add_to_emeritus",
    [
        ("re.match(r'^[-*+] \\[', l)", 'l.startswith(("- [", "* [", "+ ["))'),
        ("re.match(r'^[-*+] \\[', line)", 'line.startswith(("- [", "* [", "+ ["))'),
    ],
    "_add_to_emeritus is called only at scripts/move-to-emeritus.py:1230, inside create_emeritus_prs. A grep finds no other reference.",
    "Both member tests use the same prefix. The regex in _sort_key is unchanged.",
))

# 6. C1.S4: one pass that records the member indices
subs.append(sub(
    "C1S4-add-emeritus-one-pass", "C1.S4",
    "scripts/move-to-emeritus.py", "_add_to_emeritus",
    [
        ('''        member_lines = [l for l in lines if re.match(r'^[-*+] \\[', l)]
        member_lines.append(member_entry)
''', '''        member_idx = [i for i, l in enumerate(lines) if re.match(r'^[-*+] \\[', l)]
        member_lines = [lines[i] for i in member_idx]
        member_lines.append(member_entry)
'''),
        ('''        first_member_idx = None
        last_member_idx = None
        for i, line in enumerate(lines):
            if re.match(r'^[-*+] \\[', line):
                if first_member_idx is None:
                    first_member_idx = i
                last_member_idx = i

        if first_member_idx is not None:
            new_lines = lines[:first_member_idx] + member_lines + lines[last_member_idx + 1:]
''', '''        if member_idx:
            new_lines = lines[:member_idx[0]] + member_lines + lines[member_idx[-1] + 1:]
'''),
    ],
    "_add_to_emeritus is called only at scripts/move-to-emeritus.py:1230, inside create_emeritus_prs. A grep finds no other reference.",
    "Keeps the regex so that only the second pass is removed. Repair 5 changes the regex itself and is a different edit.",
))

# 7. C3.S5: stop scanning once every remaining actor has an event
subs.append(sub(
    "C3S5-check-events-early-exit", "C3.S5",
    "scripts/move-to-emeritus.py", "_check_events",
    [
        ('''            found.add(actor)
    return active
''', '''            found.add(actor)
            if len(found) == len(remaining):
                break
    return active
'''),
    ],
    "_check_events is called at scripts/move-to-emeritus.py:504 and :659 only. A grep finds no other reference.",
    "found holds only members of remaining and keeps each actor's first event, so the break cannot change the result. The gain is large only when every candidate is found early.",
))

with open(f"{REPO}/submissions.jsonl", "w", encoding="utf-8") as f:
    for s in subs:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")
print("wrote", len(subs))
