"""Write submissions.jsonl: each repair is the original function with one textual edit applied."""
import ast
import json
import re
import sys
from pathlib import Path

REPO = Path("/home/javad/energy-run/community")
OUT = REPO / "submissions.jsonl"


def function_source(rel_path, name):
    src = (REPO / rel_path).read_text(encoding="utf-8")
    tree = ast.parse(src)
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(nodes) == 1, (rel_path, name, len(nodes))
    return ast.get_source_segment(src, nodes[0])


def edit(text, pairs):
    for old, new in pairs:
        n = text.count(old)
        assert n == 1, (old[:70], n)
        text = text.replace(old, new)
    return text


def guard_debug(text):
    """Wrap every single-line debug(f"...") call in an `if DEBUG:` guard."""
    out = []
    for line in text.split("\n"):
        m = re.match(r'^(\s*)debug\(f"', line)
        if m:
            ind = m.group(1)
            out.append(f"{ind}if DEBUG:")
            out.append(f"{ind}    {line.strip()}")
        else:
            out.append(line)
    return "\n".join(out)


REL_VALIDATE = "scripts/validate-workstreams.py"
REL_SYNC = "scripts/gc-elections/create-github-comments.py"
REL_GEN = "scripts/gc-elections/generate-voters-roll.py"
REL_EMERITUS = "scripts/move-to-emeritus.py"

submissions = []

# 1. validate: drop the unused parent_kind lookup.
name = "validate_workstreams_semantics"
new = edit(function_source(REL_VALIDATE, name), [
    ('        parent_kind = id_to_workstream[parent_id].get("kind", "")\n\n', ""),
])
submissions.append(dict(
    id="validate-drop-parent-kind", unit=f"{REL_VALIDATE}::{name}",
    changed={f"{REL_VALIDATE}::{name}": new}, sole_caller_evidence=None,
    notes="Only the unused parent_kind assignment is removed. Nothing else in the function changes.",
))

# 2. validate: build the team sets once, before the per-workstream loop.
team_block = (
    '    teams = people_data.get("teams", {})\n'
    '    gc_members    = {u.lower() for u in teams.get("governance-committee", [])}\n'
    '    tc_members    = {u.lower() for u in teams.get("technical-committee", [])}\n'
    '    spec_sponsors = {u.lower() for u in teams.get("spec-sponsors", [])} | tc_members\n\n'
)
new = edit(function_source(REL_VALIDATE, name), [
    ('        teams = people_data.get("teams", {})\n'
     '        gc_members    = {u.lower() for u in teams.get("governance-committee", [])}\n'
     '        tc_members    = {u.lower() for u in teams.get("technical-committee", [])}\n'
     '        spec_sponsors = {u.lower() for u in teams.get("spec-sponsors", [])} | tc_members\n\n', ""),
    ('    for w in workstreams:\n        wid  = w.get("id", "(unknown)")\n',
     team_block + '    for w in workstreams:\n        wid  = w.get("id", "(unknown)")\n'),
])
submissions.append(dict(
    id="validate-hoist-team-sets", unit=f"{REL_VALIDATE}::{name}",
    changed={f"{REL_VALIDATE}::{name}": new}, sole_caller_evidence=None,
    notes="The three team sets are moved out of the per-workstream loop and built once. The statements are otherwise unchanged.",
))

# 3. sync: remove all stale handles in one regex pass per comment.
name = "sync"
new = edit(function_source(REL_SYNC, name), [
    ("        new_body = original\n"
     "        removed = []\n"
     "        for m in extract_mentions(original):\n"
     "            if m.lower() not in file_lower:\n"
     "                new_body = remove_handle_line(new_body, m)\n"
     "                removed.append(m)\n"
     "        if not removed:\n"
     "            continue\n",
     "        removed = [m for m in extract_mentions(original) if m.lower() not in file_lower]\n"
     "        if not removed:\n"
     "            continue\n"
     "        new_body = re.sub(\n"
     "            rf'^\\* @(?:{\"|\".join(re.escape(h) for h in removed)})\\s*(?:\\n|$)',\n"
     "            '', original, flags=re.MULTILINE | re.IGNORECASE,\n"
     "        )\n"),
])
submissions.append(dict(
    id="sync-single-pass-removal", unit=f"{REL_SYNC}::{name}",
    changed={f"{REL_SYNC}::{name}": new}, sole_caller_evidence=None,
    notes="Stale handles are removed with one alternation pattern per comment instead of one pass per handle. remove_handle_line is left unchanged and is no longer called from sync.",
))

# 4. sync: extract each comment's mentions once and reuse them.
new = edit(function_source(REL_SYNC, name), [
    ("    tagged_lower = set()\n"
     "    for c in voter_comments:\n"
     "        for m in extract_mentions(c.get('body') or ''):\n"
     "            tagged_lower.add(m.lower())\n",
     "    tagged_lower = set()\n"
     "    mentions_by_comment = []\n"
     "    for c in voter_comments:\n"
     "        mentions = extract_mentions(c.get('body') or '')\n"
     "        mentions_by_comment.append(mentions)\n"
     "        for m in mentions:\n"
     "            tagged_lower.add(m.lower())\n"),
    ("    for c in voter_comments:\n"
     "        original = c.get('body') or ''\n"
     "        new_body = original\n"
     "        removed = []\n"
     "        for m in extract_mentions(original):\n",
     "    for c, mentions in zip(voter_comments, mentions_by_comment):\n"
     "        original = c.get('body') or ''\n"
     "        new_body = original\n"
     "        removed = []\n"
     "        for m in mentions:\n"),
])
submissions.append(dict(
    id="sync-reuse-mentions", unit=f"{REL_SYNC}::{name}",
    changed={f"{REL_SYNC}::{name}": new}, sole_caller_evidence=None,
    notes="The mentions found while building tagged_lower are kept per comment and reused in the removal loop, so each body is scanned once for mentions.",
))

# 5. get_github_login: reuse one HTTP session.
name = "get_github_login"
new = edit(function_source(REL_GEN, name), [
    ("def get_github_login(username):", "def get_github_login(username, session=requests.Session()):"),
    ("    response = requests.get(url, headers=headers)", "    response = session.get(url, headers=headers)"),
])
submissions.append(dict(
    id="gh-login-session", unit=f"{REL_GEN}::{name}",
    changed={f"{REL_GEN}::{name}": new}, sole_caller_evidence=None,
    notes="A requests.Session is created once, as a default argument, and reused across calls. The only caller is build_devstats_rows, which passes no session.",
))

# 6. _get_repo_commenters: set membership for the duplicate check.
name = "_get_repo_commenters"
new = edit(function_source(REL_EMERITUS, name), [
    ("    commenters = {}\n", "    commenters = {}\n    seen = set()\n"),
    ('            if number and number not in commenters[user][kind]:\n'
     '                commenters[user][kind].append(number)\n',
     '            if number and (user, kind, number) not in seen:\n'
     '                seen.add((user, kind, number))\n'
     '                commenters[user][kind].append(number)\n'),
])
submissions.append(dict(
    id="commenters-set-membership", unit=f"{REL_EMERITUS}::{name}",
    changed={f"{REL_EMERITUS}::{name}": new}, sole_caller_evidence=None,
    notes="The duplicate check uses a set of (user, kind, number) keys. The lists in the returned dict keep their order and contents.",
))

# 7. _check_events: stop once every remaining user has been found.
name = "_check_events"
new = edit(function_source(REL_EMERITUS, name), [
    ("    for actor, event_type, issue_number in all_events:\n"
     "        if actor in remaining and actor not in found and event_type in event_types:\n",
     "    for actor, event_type, issue_number in all_events:\n"
     "        if len(found) == len(remaining):\n"
     "            break\n"
     "        if actor in remaining and actor not in found and event_type in event_types:\n"),
])
submissions.append(dict(
    id="events-stop-when-all-found", unit=f"{REL_EMERITUS}::{name}",
    changed={f"{REL_EMERITUS}::{name}": new}, sole_caller_evidence=None,
    notes="The loop stops once every user in remaining is in found. found only holds members of remaining, so no later event could add to the result.",
))

# 8. _verify_review_candidates: fetch each candidate PR's reviews once per run.
name = "_verify_review_candidates"
new = '''def _verify_review_candidates(user, candidate_prs, repo, cutoff, _reviews_cache={}):
    """Verify candidate PRs via REST to confirm actual review dates.

    Returns the first PR number with a confirmed recent review, or None.
    Reviews are cached per (repo, PR) for the whole run.
    """
    for pr_number in candidate_prs:
        key = (repo, pr_number)
        if key not in _reviews_cache:
            reviews_url = f"{REST_API}/repos/{ORG}/{repo}/pulls/{pr_number}/reviews"
            rev_resp = request_with_retry("GET", reviews_url)
            _reviews_cache[key] = read_json(rev_resp)
        for review in _reviews_cache[key]:
            submitted = review.get("submitted_at", "")[:10]
            reviewer = (review.get("user") or {}).get("login", "")
            if reviewer == user and submitted >= cutoff:
                return pr_number
    return None
'''
submissions.append(dict(
    id="verify-reviews-cache", unit=f"{REL_EMERITUS}::{name}",
    changed={f"{REL_EMERITUS}::{name}": new}, sole_caller_evidence=None,
    notes="The reviews of each (repo, PR) are kept in a dict that is a default argument, so it lives for the whole run and is read only in this function.",
))

# 9-11. debug calls guarded by DEBUG in the three activity checks.
for label, name in [("triager", "check_triager_activity"),
                    ("approver", "check_approver_activity"),
                    ("maintainer", "check_maintainer_activity")]:
    new = guard_debug(function_source(REL_EMERITUS, name))
    submissions.append(dict(
        id=f"{label}-guard-debug", unit=f"{REL_EMERITUS}::{name}",
        changed={f"{REL_EMERITUS}::{name}": new}, sole_caller_evidence=None,
        notes=f"Each debug() call in {name} is wrapped in `if DEBUG:`, so its f-string is built only when debugging is on. debug() itself is unchanged.",
    ))

# 12. _add_to_emeritus: find the member lines and their first and last index in one pass.
name = "_add_to_emeritus"
new = edit(function_source(REL_EMERITUS, name), [
    ("        member_lines = [l for l in lines if re.match(r'^[-*+] \\[', l)]\n"
     "        member_lines.append(member_entry)\n",
     "        member_lines = []\n"
     "        first_member_idx = None\n"
     "        last_member_idx = None\n"
     "        for i, line in enumerate(lines):\n"
     "            if re.match(r'^[-*+] \\[', line):\n"
     "                member_lines.append(line)\n"
     "                if first_member_idx is None:\n"
     "                    first_member_idx = i\n"
     "                last_member_idx = i\n"
     "        member_lines.append(member_entry)\n"),
    ("        first_member_idx = None\n"
     "        last_member_idx = None\n"
     "        for i, line in enumerate(lines):\n"
     "            if re.match(r'^[-*+] \\[', line):\n"
     "                if first_member_idx is None:\n"
     "                    first_member_idx = i\n"
     "                last_member_idx = i\n"
     "\n",
     ""),
])
submissions.append(dict(
    id="add-emeritus-single-scan", unit=f"{REL_EMERITUS}::{name}",
    changed={f"{REL_EMERITUS}::{name}": new}, sole_caller_evidence=None,
    notes="The member-line regex runs once per section line instead of twice. The member list, the indices and the rebuilt text are unchanged.",
))

OUT.write_text("".join(json.dumps(s, ensure_ascii=False) + "\n" for s in submissions), encoding="utf-8")
print(f"wrote {len(submissions)} submissions to {OUT}")
