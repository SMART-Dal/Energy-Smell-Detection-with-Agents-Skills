import ast, json, sys
from pathlib import Path

REPO = Path("/home/javad/energy-run/community")
OUT = REPO / "submissions.jsonl"


def function_source(relpath, name):
    text = (REPO / relpath).read_text(encoding="utf-8")
    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)
    matches = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    assert len(matches) == 1, (relpath, name, len(matches))
    node = matches[0]
    start = min([node.lineno] + [d.lineno for d in node.decorator_list]) - 1
    return "".join(lines[start:node.end_lineno]).rstrip("\n") + "\n"


def edit(src, pairs):
    for old, new in pairs:
        n = src.count(old)
        assert n == 1, (n, old[:80])
        src = src.replace(old, new)
    return src


SUBS = []


def add(id_, root, relpath, name, pairs, evidence, notes):
    unit = f"{relpath}::{name}"
    new = edit(function_source(relpath, name), pairs)
    SUBS.append({
        "id": id_,
        "root_cause": root,
        "unit": unit,
        "changed": {unit: new},
        "sole_caller_evidence": evidence,
        "notes": notes,
        "agent_measurement": None,
    })


V = "scripts/validate-workstreams.py"
M = "scripts/move-to-emeritus.py"
G = "scripts/gc-elections/generate-voters-roll.py"
B = "scripts/baremetal-runner-report.py"

# 1. validate: hoist the three membership sets out of the per-workstream loop
add(
    "C3S2-validate-hoist-sets", "C3.S2", V, "validate_workstreams_semantics",
    [
        ('''        teams = people_data.get("teams", {})
        gc_members    = {u.lower() for u in teams.get("governance-committee", [])}
        tc_members    = {u.lower() for u in teams.get("technical-committee", [])}
        spec_sponsors = {u.lower() for u in teams.get("spec-sponsors", [])} | tc_members

''', ""),
         ('''    for w in workstreams:
        wid  = w.get("id", "(unknown)")

        person_roles''', '''    teams = people_data.get("teams", {})
    gc_members    = {u.lower() for u in teams.get("governance-committee", [])}
    tc_members    = {u.lower() for u in teams.get("technical-committee", [])}
    spec_sponsors = {u.lower() for u in teams.get("spec-sponsors", [])} | tc_members

    for w in workstreams:
        wid  = w.get("id", "(unknown)")

        person_roles'''),
    ],
    "validate_workstreams_semantics is called only from main() at scripts/validate-workstreams.py:184. The three sets are locals built from people_data, which the function only reads.",
    "Hoists gc_members, tc_members and spec_sponsors above the workstream loop. Edge to watch: with an empty workstreams list and people_data None, .get now runs before the loop.",
)

# 2. validate: delete the unread parent_kind assignment
add(
    "C1S1-validate-dead-parent-kind", "C1.S1", V, "validate_workstreams_semantics",
    [
        ('''        parent_kind = id_to_workstream[parent_id].get("kind", "")

''', ""),
    ],
    "parent_kind is a local assigned at line 103 and read nowhere in the function. The lookup cannot raise because the parent id was checked against id_to_workstream just above.",
    "Deletes the parent_kind line only. The unused kind variable at the top of the first loop is a separate dead store and is not touched here.",
)

# 3. _check_events: stop once every remaining user has been found
add(
    "C3S5-check-events-break", "C3.S5", M, "_check_events",
    [
        ('''            found.add(actor)
''', '''            found.add(actor)
            if len(found) == len(remaining):
                break
'''),
    ],
    "Called only at move-to-emeritus.py:504 and :659, both with a set for remaining. The break fires only when every entry of remaining is in found, after which no later event can add to active.",
    "Adds an early break once len(found) equals len(remaining).",
)

# 4. _get_repo_commenters: set beside the per-user lists
add(
    "C5S2-commenters-seen-set", "C5.S2", M, "_get_repo_commenters",
    [
        ('''    commenters = {}
''', '''    commenters = {}
    seen = set()
'''),
        ('''            if number and number not in commenters[user][kind]:
                commenters[user][kind].append(number)
''', '''            if number and (user, kind, number) not in seen:
                seen.add((user, kind, number))
                commenters[user][kind].append(number)
'''),
    ],
    "Called only from _check_comments (move-to-emeritus.py:315). The returned dict and its list order are unchanged; seen is a local.",
    "Replaces the linear list membership test with a set of (user, kind, number) built alongside the lists.",
)

# 5. _add_to_emeritus: match each line once
add(
    "C1S4-add-emeritus-single-match", "C1.S4", M, "_add_to_emeritus",
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
''', '''        first_member_idx = member_idx[0] if member_idx else None
        last_member_idx = member_idx[-1] if member_idx else None
'''),
    ],
    "Called only at move-to-emeritus.py:1230 (create_emeritus_prs). The function is pure on its arguments.",
    "One pass over the section lines records the member indices, which replaces the two separate re.match passes.",
)

# 6. _verify_review_candidates: fetch each PR's reviews once per process
add(
    "C8S4-verify-review-cache", "C8.S4", M, "_verify_review_candidates",
    [
        ('''    for pr_number in candidate_prs:
        reviews_url = f"{REST_API}/repos/{ORG}/{repo}/pulls/{pr_number}/reviews"
        rev_resp = request_with_retry("GET", reviews_url)
        reviews = read_json(rev_resp)
''', '''    cache = _verify_review_candidates.__dict__.setdefault("reviews", {})
    for pr_number in candidate_prs:
        reviews_url = f"{REST_API}/repos/{ORG}/{repo}/pulls/{pr_number}/reviews"
        if (repo, pr_number) not in cache:
            cache[(repo, pr_number)] = read_json(request_with_retry("GET", reviews_url))
        reviews = cache[(repo, pr_number)]
'''),
    ],
    "Called at move-to-emeritus.py:397 and :455 only, and both take the same return value. The cache is a function attribute that only this function reads.",
    "Caches each PR's review list per (repo, pr). A module-level name cannot come in through a function repair, so the cache lives on the function object.",
)

# 7. _get_repo_events: keep only the event types the checks read
add(
    "C9S2-events-keep-consumed-types", "C9.S2", M, "_get_repo_events",
    [
        ('''    results = []
''', '''    results = []
    consumed = {"labeled", "unlabeled", "closed", "merged"}
'''),
        ('''            actor = (event.get("actor") or {}).get("login", "")
            issue_number = (event.get("issue") or {}).get("number", "")
            if actor:
                results.append((actor, event.get("event", ""), issue_number))
''', '''            actor = (event.get("actor") or {}).get("login", "")
            issue_number = (event.get("issue") or {}).get("number", "")
            event_type = event.get("event", "")
            if actor and event_type in consumed:
                results.append((actor, event_type, issue_number))
'''),
    ],
    "Called only from _check_events (move-to-emeritus.py:340). _check_events is called with {labeled, unlabeled, closed} and {merged}, so the four types kept here cover every type it reads. The _repo_events_cache contents change, and only _get_repo_events reads that cache.",
    "Stores only the four event types that _check_events uses. The request pages are unchanged because the endpoint has no type filter.",
)

# 8. main: drop the team_repos_map store nothing reads
add(
    "C1S1-main-team-repos-map", "C1.S1", M, "main",
    [
        ('''    team_repos_map = {}  # team_name -> set(repos)
''', ""),
        ('''            # Record team -> repos mapping
            team_repos_map[name] = set(repos)

''', ""),
    ],
    "team_repos_map is local to main and read nowhere in main or in any callee.",
    "Removes the dict, its store and its comment. The per-team repos set is still built where all_user_data uses it.",
)

# 9. get_github_login: keep one HTTP session across calls
add(
    "C9S1-login-session", "C9.S1", G, "get_github_login",
    [
        ('''    response = requests.get(url, headers=headers)
''', '''    session = get_github_login.__dict__.get("session")
    if session is None:
        session = get_github_login.session = requests.Session()
    response = session.get(url, headers=headers)
'''),
    ],
    "Called only from build_devstats_rows (generate-voters-roll.py:94). The session is a function attribute read only here.",
    "requests.get opens a fresh connection per call; a session reuses the pooled connection. The sleep and the request headers are unchanged. The session is never closed, which is acceptable for a one-shot script.",
)

# 10. collect_jobs: parse each run's start once, not once per job
add(
    "C3S2-collect-jobs-parse-run-start-once", "C3.S2", B, "collect_jobs",
    [
        ('''            run_started_at = run.get("run_started_at") or run.get("created_at")
''', '''            run_started_at = run.get("run_started_at") or run.get("created_at")
            run_start = None
            if run_started_at:
                try:
                    run_start = parse_iso(run_started_at)
                except ValueError:
                    run_start = None
'''),
        ('''                qwait = 0.0
                if run_started_at:
                    try:
                        qwait = max(
                            0.0,
                            (parse_iso(started) - parse_iso(run_started_at))
                            .total_seconds(),
                        )
                    except ValueError:
                        qwait = 0.0
''', '''                qwait = 0.0
                if run_start is not None:
                    try:
                        qwait = max(
                            0.0,
                            (parse_iso(started) - run_start).total_seconds(),
                        )
                    except ValueError:
                        qwait = 0.0
'''),
    ],
    "Called only from main() at baremetal-runner-report.py:196. run_start is local to collect_jobs.",
    "A malformed run start still gives qwait 0.0 for every job of that run. Edge: a non-string run start that raised TypeError would now raise before the job loop rather than inside it.",
)

# 11. _check_reviews: compute each user's alias once
add(
    "C8S2-check-reviews-alias-once", "C8.S2", M, "_check_reviews",
    [
        ('''        aliases = []
        for user in batch_users:
            safe = "u_" + re.sub(r"[^a-zA-Z0-9]", "_", user)
''', '''        aliases = []
        safe_names = {}
        for user in batch_users:
            safe = safe_names[user] = "u_" + re.sub(r"[^a-zA-Z0-9]", "_", user)
'''),
        ('''            safe = "u_" + re.sub(r"[^a-zA-Z0-9]", "_", user)
            result = data["data"]''', '''            safe = safe_names[user]
            result = data["data"]'''),
    ],
    "Called at move-to-emeritus.py:557 and :613, both with the same return contract. safe_names is local.",
    "Keeps the alias built for the query and reads it when the result is matched, instead of calling re.sub twice per user.",
)

# 12. check_maintainer_activity: same alias reuse
add(
    "C8S2-check-maintainer-alias-once", "C8.S2", M, "check_maintainer_activity",
    [
        ('''            aliases = []
            for user in batch_users:
                safe = "u_" + re.sub(r"[^a-zA-Z0-9]", "_", user)
''', '''            aliases = []
            safe_names = {}
            for user in batch_users:
                safe = safe_names[user] = "u_" + re.sub(r"[^a-zA-Z0-9]", "_", user)
'''),
        ('''                safe = "u_" + re.sub(r"[^a-zA-Z0-9]", "_", user)
                authored_result''', '''                safe = safe_names[user]
                authored_result'''),
    ],
    "Reached through check_fns (move-to-emeritus.py:1297) and ROLES (line 685); the signature and return set are unchanged. safe_names is local.",
    "Same alias reuse as _check_reviews, for the authored-PR batch.",
)

# 13. _parse_members: comprehension in place of the append loop
add(
    "C10S3-parse-members-comprehension", "C10.S3", M, "_parse_members",
    [
        ('''    members = []
    for m in member_re.finditer(text):
        members.append({
            "name": m.group(1),
            "username": m.group(2),
            "line": m.group(0),
        })
    return members
''', '''    return [
        {
            "name": m.group(1),
            "username": m.group(2),
            "line": m.group(0),
        }
        for m in member_re.finditer(text)
    ]
'''),
    ],
    "Called only at move-to-emeritus.py:1210 (create_emeritus_prs). Returns the same list of dicts.",
    "The loop body is only the dict construction, so the comprehension does the same work without a bound-method lookup and call per member.",
)

# 14. create_emeritus_prs: lower the user name once per section
add(
    "C3S2-create-emeritus-lower-once", "C3.S2", M, "create_emeritus_prs",
    [
        ('''                    for m in _parse_members(section_text):
                        if m["username"].lower() == user.lower():
''', '''                    user_lower = user.lower()
                    for m in _parse_members(section_text):
                        if m["username"].lower() == user_lower:
'''),
    ],
    "Called only from main() at move-to-emeritus.py:1500. user is not rebound inside the inner loop, so user_lower is the same value on every pass.",
    "Hoists user.lower() above the member loop it is compared in.",
)

with OUT.open("w", encoding="utf-8") as f:
    for s in SUBS:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")
print(len(SUBS), "submissions written")
