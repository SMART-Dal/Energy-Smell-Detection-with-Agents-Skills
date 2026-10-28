import ast, json, textwrap
def src(path, qual):
    t=open(path).read(); tree=ast.parse(t); lines=t.splitlines(keepends=True)
    parts=qual.split("."); nodes=tree.body
    for i,p in enumerate(parts):
        n=[x for x in nodes if getattr(x,"name",None)==p][0]
        nodes=getattr(n,"body",[])
    start=(n.decorator_list[0].lineno if n.decorator_list else n.lineno)-1
    return "".join(lines[start:n.end_lineno]).rstrip("\n")
def rep(s, old, new):
    assert s.count(old)==1,(old,s.count(old)); return s.replace(old,new)
subs=[]
def add(id,unit,changed,evid,notes):
    subs.append({"id":id,"unit":unit,"changed":changed,"sole_caller_evidence":evid,"notes":notes})

# 1 validate hoist
p="scripts/validate-workstreams.py"; q="validate_workstreams_semantics"; s=src(p,q)
old='''    for w in workstreams:
        wid  = w.get("id", "(unknown)")

        person_roles = {next(iter(pr)) for pr in w.get("people", [])}'''
new='''    gc_members = None
    for w in workstreams:
        wid  = w.get("id", "(unknown)")

        person_roles = {next(iter(pr)) for pr in w.get("people", [])}'''
s1=rep(s,old,new)
old2='''        teams = people_data.get("teams", {})
        gc_members    = {u.lower() for u in teams.get("governance-committee", [])}
        tc_members    = {u.lower() for u in teams.get("technical-committee", [])}
        spec_sponsors = {u.lower() for u in teams.get("spec-sponsors", [])} | tc_members
'''
new2='''        if gc_members is None:
            teams = people_data.get("teams", {})
            gc_members    = {u.lower() for u in teams.get("governance-committee", [])}
            tc_members    = {u.lower() for u in teams.get("technical-committee", [])}
            spec_sponsors = {u.lower() for u in teams.get("spec-sponsors", [])} | tc_members
'''
s1=rep(s1,old2,new2)
add("validate-team-sets",p+"::"+q,{p+"::"+q:s1},None,"Team sets are built on the first workstream and reused; people_data is never mutated in the function, so the sets are identical every iteration. Lazy so an empty workstreams list never touches people_data, as before.")
# 1b dead lookup
s2=rep(s,'''
        parent_kind = id_to_workstream[parent_id].get("kind", "")
''','''
''')
add("validate-dead-parent-kind",p+"::"+q,{p+"::"+q:s2},None,"Removes the unused `parent_kind` assignment; the key is known present from the check above it.")

# 2 render_table
p="scripts/baremetal-runner-report.py"; q="render_table"; s=src(p,q)
t=rep(s,'''        lambda: {"runs": set(), "total": 0.0,''','''        lambda: {"total": 0.0,''')
t=rep(t,'''        a["runs"].add(r["run_id"])
''','')
t=rep(t,'n_runs = len(v["runs"])','n_runs = len(v["run_totals"])')
add("render-table-runs-set",p+"::"+q,{p+"::"+q:t},None,"`runs` was a set of run ids identical to the keys of `run_totals`, which is updated on the same record.")

# 3 collect_jobs
q="collect_jobs"; s=src(p,q)
t=rep(s,'''            run_started_at = run.get("run_started_at") or run.get("created_at")
''','''            run_started_at = run.get("run_started_at") or run.get("created_at")
            try:
                run_started_dt = parse_iso(run_started_at) if run_started_at else None
            except ValueError:
                run_started_dt = False
''')
t=rep(t,'''                try:
                    dur = (parse_iso(completed) - parse_iso(started)).total_seconds()
                except ValueError:
                    continue''','''                try:
                    started_dt = parse_iso(started)
                    dur = (parse_iso(completed) - started_dt).total_seconds()
                except ValueError:
                    continue''')
t=rep(t,'''                if run_started_at:
                    try:
                        qwait = max(
                            0.0,
                            (parse_iso(started) - parse_iso(run_started_at))
                            .total_seconds(),
                        )
                    except ValueError:
                        qwait = 0.0''','''                if run_started_dt:
                    qwait = max(
                        0.0,
                        (started_dt - run_started_dt).total_seconds(),
                    )''')
t=rep(t,'"started": parse_iso(started),','"started": started_dt,')
add("collect-jobs-parse-once",p+"::"+q,{p+"::"+q:t},None,"Parses started once per job and run_started_at once per run. Unparseable run_started_at gives qwait 0.0 as before (run_started_dt False). Edge: original parsed started before run_started_at failing; both orders only matter via ValueError which is caught identically, except started aware/naive mixing TypeError which is unchanged.")

# 4 sync
p="scripts/gc-elections/create-github-comments.py"; q="sync"; s=src(p,q)
t=rep(s,'''        removed = []
        for m in extract_mentions(original):
            if m.lower() not in file_lower:
                new_body = remove_handle_line(new_body, m)
                removed.append(m)
        if not removed:
            continue
''','''        removed = []
        for m in extract_mentions(original):
            if m.lower() not in file_lower:
                removed.append(m)
        if not removed:
            continue
        stale = '|'.join(re.escape(h) for h in dict.fromkeys(removed))
        new_body = re.sub(
            rf'^\\* @(?:{stale})\\s*(?:\\n|$)', '', original,
            flags=re.MULTILINE | re.IGNORECASE,
        )
''')
add("sync-single-pass-removal",p+"::"+q,{p+"::"+q:t},None,"One alternation regex over the original body replaces k sequential remove_handle_line calls. remove_handle_line is still defined and used nowhere else in the repo (grep).")
t=rep(s,'''    tagged_lower = set()
    for c in voter_comments:
        for m in extract_mentions(c.get('body') or ''):
            tagged_lower.add(m.lower())
''','''    tagged_lower = set()
    mentions_by_comment = []
    for c in voter_comments:
        mentions = extract_mentions(c.get('body') or '')
        mentions_by_comment.append(mentions)
        for m in mentions:
            tagged_lower.add(m.lower())
''')
t=rep(t,'''    for c in voter_comments:
        original = c.get('body') or ''
        new_body = original
        removed = []
        for m in extract_mentions(original):''','''    for c, mentions in zip(voter_comments, mentions_by_comment):
        original = c.get('body') or ''
        new_body = original
        removed = []
        for m in mentions:''')
add("sync-mentions-once",p+"::"+q,{p+"::"+q:t},None,"extract_mentions on each original body is computed once in the tagging pass and reused in the stale pass. Bodies are not mutated between the passes (new_body is a separate string).")

# 5 is_voter_comment
q="is_voter_comment"; s=src(p,q)
t=rep(s,'''    lines = body.splitlines()''','''    if HEADER not in body:
        return False
    lines = body.splitlines()''')
add("voter-comment-header-prefilter",p+"::"+q,{p+"::"+q:t},None,"If HEADER is not a substring of body, no line can equal HEADER after strip, so False is returned early. Behaviour otherwise unchanged. Edge: non-str body that is truthy would have failed at splitlines (AttributeError); `in` raises TypeError for non-str non-container, so exception type may differ for such inputs.")

# 6 _get_repo_commenters
p="scripts/move-to-emeritus.py"; q="_get_repo_commenters"; s=src(p,q)
t=rep(s,'''    commenters = {}
    url =''','''    commenters = {}
    seen = set()
    url =''')
t=rep(t,'''            if number and number not in commenters[user][kind]:
                commenters[user][kind].append(number)''','''            if number and (user, kind, number) not in seen:
                seen.add((user, kind, number))
                commenters[user][kind].append(number)''')
add("commenters-seen-set",p+"::"+q,{p+"::"+q:t},None,"Local `seen` set replaces the list membership test; lists keep first-seen order. Early-return path stores the same dict in the cache.")

# 7 _add_to_emeritus
q="_add_to_emeritus"; s=src(p,q)
t=rep(s,'''        # Separate member lines from non-member lines
        member_lines = [l for l in lines if re.match(r'^[-*+] \\[', l)]
        member_lines.append(member_entry)
''','''        # Separate member lines from non-member lines
        member_idxs = [i for i, l in enumerate(lines) if re.match(r'^[-*+] \\[', l)]
        member_lines = [lines[i] for i in member_idxs]
        member_lines.append(member_entry)
''')
t=rep(t,'''        first_member_idx = None
        last_member_idx = None
        for i, line in enumerate(lines):
            if re.match(r'^[-*+] \\[', line):
                if first_member_idx is None:
                    first_member_idx = i
                last_member_idx = i
''','''        first_member_idx = member_idxs[0] if member_idxs else None
        last_member_idx = member_idxs[-1] if member_idxs else None
''')
add("emeritus-single-match-pass",p+"::"+q,{p+"::"+q:t},None,"Records member line indexes during the first regex pass and takes first/last from them instead of re-matching every line.")

# 8 render_group
p="scripts/update-sig-tables.py"
s=src(p,"extract_row_data"); g=src(p,"render_group")
e=rep(s,"def extract_row_data(ws):","def extract_row_data(ws, with_people=True):")
e=rep(e,'''    gc_liaisons = []
    tc_sponsors = []
    spec_sponsors = []

    for entry in ws.get("people", []):''','''    gc_liaisons = []
    tc_sponsors = []
    spec_sponsors = []

    for entry in (ws.get("people", []) if with_people else []):''')
e=rep(e,'''    if ws.get("tcSponsorship") == "collective":''','''    if with_people and ws.get("tcSponsorship") == "collective":''')
g2=rep(g,"data = extract_row_data(ws)","data = extract_row_data(ws, with_people=False)")
add("render-group-skip-people",p+"::render_group",{p+"::extract_row_data":e,p+"::render_group":g2},"grep -rn extract_row_data /home/javad/energy-run/community --include=*.py: only called in render_group and render_sig_details; the new keyword defaults to True so render_sig_details is unchanged.","render_group reads only meeting_schedule, calendar and slack_channels from the dict. Edge: malformed people entries (e.g. tcSponsor missing username) no longer raise inside render_group; the same ws raises later in render_sig_details in the real program.")

with open("submissions.jsonl","w") as f:
    for x in subs:
        x["agent_measurement"]=None
        f.write(json.dumps(x)+"\n")
print(len(subs))
