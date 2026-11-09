import ast, json, sys
def src(path, name):
    t = open(path).read(); tree = ast.parse(t); lines = t.splitlines(keepends=True)
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name == name:
            start = (n.decorator_list[0].lineno if n.decorator_list else n.lineno) - 1
            return "".join(lines[start:n.end_lineno])
    raise KeyError(name)
M="scripts/move-to-emeritus.py"; V="scripts/validate-workstreams.py"; G="scripts/update-sig-tables.py"
C="scripts/gc-elections/create-github-comments.py"; B="scripts/baremetal-runner-report.py"; S="scripts/generate-sponsorship-ledger.py"
subs=[]
def sub(id_, rc, path, name, reps, notes, ev=None):
    s = src(path, name)
    for old, new in reps:
        assert s.count(old)==1, (id_, old, s.count(old))
        s = s.replace(old, new)
    subs.append({"id":id_,"root_cause":rc,"unit":f"{path}::{name}","changed":{f"{path}::{name}":s},"sole_caller_evidence":ev,"notes":notes})

sub("C3S5-check-events","C3.S5",M,"_check_events",[(
"            found.add(actor)\n","            found.add(actor)\n            if len(found) == len(remaining):\n                break\n")],
"Stops the scan once every user in `remaining` has a hit; later events cannot add entries.")
sub("C5S1-commenters-seen","C5.S1",M,"_get_repo_commenters",[
("    commenters = {}\n","    commenters = {}\n    seen = set()\n"),
("            if number and number not in commenters[user][kind]:\n                commenters[user][kind].append(number)\n",
 "            if number and (user, kind, number) not in seen:\n                seen.add((user, kind, number))\n                commenters[user][kind].append(number)\n")],
"Local set answers the duplicate test; output lists keep insertion order.")
body_old_pr="""    for user, role_label, teams in sorted(changes):
        teams_str = ", ".join(teams)
        body += f"- @{user} ({role_label}, Remove from team(s): {teams_str})\\n"
"""
body_new="""    body += "".join(
        f"- @{user} ({role_label}, Remove from team(s): {', '.join(teams)})\\n"
        for user, role_label, teams in sorted(changes)
    )
"""
sub("C10S4-pr-body","C10.S4",M,"_build_pr_body",[(body_old_pr,body_new)],"Join the per-member lines once.")
sub("C10S4-issue-body","C10.S4",M,"_build_issue_body",[(body_old_pr,body_new)],"Join the per-member lines once.")
sub("C1S4-add-emeritus-single-pass","C1.S4",M,"_add_to_emeritus",[
("""        member_lines = [l for l in lines if re.match(r'^[-*+] \\[', l)]
        member_lines.append(member_entry)
""","""        member_lines = []
        first_member_idx = None
        last_member_idx = None
        for i, line in enumerate(lines):
            if re.match(r'^[-*+] \\[', line):
                member_lines.append(line)
                if first_member_idx is None:
                    first_member_idx = i
                last_member_idx = i
        member_lines.append(member_entry)
"""),
("""        first_member_idx = None
        last_member_idx = None
        for i, line in enumerate(lines):
            if re.match(r'^[-*+] \\[', line):
                if first_member_idx is None:
                    first_member_idx = i
                last_member_idx = i

""","")],"One pass records member lines and first/last index instead of two regex passes.")
sub("C8S3-add-emeritus-compiled","C8.S3",M,"_add_to_emeritus",[
("        lines = section_text.split(\"\\n\")\n","        lines = section_text.split(\"\\n\")\n        member_start = re.compile(r'^[-*+] \\[')\n        member_name = re.compile(r'^[-*+] \\[([^\\]]+)\\]')\n"),
("[l for l in lines if re.match(r'^[-*+] \\[', l)]","[l for l in lines if member_start.match(l)]"),
("m = re.match(r'^[-*+] \\[([^\\]]+)\\]', line)","m = member_name.match(line)"),
("            if re.match(r'^[-*+] \\[', line):\n                if first","            if member_start.match(line):\n                if first")],
"Compile the member patterns once per call; separate edit from the single-pass repair.")
sub("C3S1-parse-members-comp","C3.S1",M,"_parse_members",[(
"""    members = []
    for m in member_re.finditer(text):
        members.append({
            "name": m.group(1),
            "username": m.group(2),
            "line": m.group(0),
        })
    return members
""","""    return [
        {"name": m.group(1), "username": m.group(2), "line": m.group(0)}
        for m in member_re.finditer(text)
    ]
""")],"Append loop becomes a comprehension.")
sub("C3S2-validate-hoist-sets","C3.S2",V,"validate_workstreams_semantics",[(
"""        teams = people_data.get("teams", {})
        gc_members    = {u.lower() for u in teams.get("governance-committee", [])}
        tc_members    = {u.lower() for u in teams.get("technical-committee", [])}
        spec_sponsors = {u.lower() for u in teams.get("spec-sponsors", [])} | tc_members

""",""),
("""    for w in workstreams:
        wid  = w.get("id", "(unknown)")

        person_roles""","""    if workstreams:
        teams = people_data.get("teams", {})
        gc_members    = {u.lower() for u in teams.get("governance-committee", [])}
        tc_members    = {u.lower() for u in teams.get("technical-committee", [])}
        spec_sponsors = {u.lower() for u in teams.get("spec-sponsors", [])} | tc_members

    for w in workstreams:
        wid  = w.get("id", "(unknown)")

        person_roles""")],"Team sets built once; guarded by `if workstreams` so an empty list never touches people_data.")
sub("C1S1-validate-parent-kind","C1.S1",V,"validate_workstreams_semantics",[(
"""        parent_kind = id_to_workstream[parent_id].get("kind", "")
""","")],"Delete the unread `parent_kind` lookup.")
sub("C1S5-render-group-light","C1.S5",G,"render_group",[(
"        data = extract_row_data(ws)\n","""        meeting_schedule = ""
        calendar = ""
        slack_channels = []
        for res in ws.get("resources", []):
            if "meeting" in res:
                m = res["meeting"]
                meeting_schedule = m.get("schedule", "")
                if cal := m.get("calendarInviteGroup"):
                    calendar = f"[{cal}](https://groups.google.com/a/opentelemetry.io/g/{cal})"
            elif "slack" in res:
                s = res["slack"]
                slack_channels.append(f"[{s['name']}](https://cloud-native.slack.com/archives/{s['id']})")
"""),
("{data['meeting_schedule']} | {data['calendar']} | {join_details(data['slack_channels'])}","{meeting_schedule} | {calendar} | {join_details(slack_channels)}")],
"Only schedule, calendar and slack are rendered, so the other link lists are not built. Reproduces the original's first-matching-branch dispatch for those keys.")
sub("C10S4-render-group-join","C10.S4",G,"render_group",[
("""    content = f"### {group_name}\\n\\n"
    content += "| Name""","""    rows = []
    content = f"### {group_name}\\n\\n"
    content += "| Name"""),
("""        content += f"| {name} | {data['meeting_schedule']} | {data['calendar']} | {join_details(data['slack_channels'])} | {details} |\\n"

    content += "\\n"
""","""        rows.append(f"| {name} | {data['meeting_schedule']} | {data['calendar']} | {join_details(data['slack_channels'])} | {details} |\\n")

    content += "".join(rows)
    content += "\\n"
""")],"Rows collected and joined once.")
sub("C10S4-sig-details-join","C10.S4",G,"render_sig_details_group",[(
"""    content = f"## {group_name}\\n\\n"
    for ws in sigs:
        content += render_sig_details(ws)
    return content
""","""    return f"## {group_name}\\n\\n" + "".join(render_sig_details(ws) for ws in sigs)
""")],"Join per-SIG blocks once.")
sub("C1S4-sync-mentions-once","C1.S4",C,"sync",[(
"""    tagged_lower = set()
    for c in voter_comments:
        for m in extract_mentions(c.get('body') or ''):
            tagged_lower.add(m.lower())
""","""    mentions_by_comment = [extract_mentions(c.get('body') or '') for c in voter_comments]
    tagged_lower = set()
    for mentions_in_comment in mentions_by_comment:
        for m in mentions_in_comment:
            tagged_lower.add(m.lower())
"""),
("""    for c in voter_comments:
        original = c.get('body') or ''""","""    for c, mentions_in_comment in zip(voter_comments, mentions_by_comment):
        original = c.get('body') or ''"""),
("        for m in extract_mentions(original):\n            if m.lower() not in file_lower:","        for m in mentions_in_comment:\n            if m.lower() not in file_lower:")],
"Each body is scanned for mentions once and the list reused by the stale pass.")
sub("C6S1-render-table-runs","C6.S1",B,"render_table",[
("""        lambda: {"runs": set(), "total": 0.0,""","""        lambda: {"total": 0.0,"""),
("        a[\"runs\"].add(r[\"run_id\"])\n",""),
("n_runs = len(v[\"runs\"])","n_runs = len(v[\"run_totals\"])")],
"The `runs` set always equals run_totals' keys, so it is dropped.")
sub("C6S2-rank-gc-sorted","C6.S2",S,"rank_gc",[(
"""    items = list(load.items())
    items.sort(key=lambda kv: (-len(kv[1]), kv[0]))
    return items
""","""    return sorted(load.items(), key=lambda kv: (-len(kv[1]), kv[0]))
""")],"sorted() builds the list once instead of copy then sort.")
open("submissions.jsonl","w").write("\n".join(json.dumps(s) for s in [dict(s, **{}) for s in subs])+"\n")
print(len(subs))
