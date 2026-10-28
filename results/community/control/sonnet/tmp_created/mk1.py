import json
S=lambda l,ls,w:{"label":l,"lines":ls,"why":w}
recs=[
("scripts/validate-workstreams.py::validate_workstreams_semantics",[
 S("a",[126,127,128,129],"`teams`, `gc_members`, `tc_members` and `spec_sponsors` are rebuilt (three set comprehensions with .lower() over the team lists) inside the `for w in workstreams` loop although they depend only on `people_data`"),
 S("b",[103],"`parent_kind` is looked up per workstream and never read"),
 S("c",[105,106,107,108,109,110,111,112,113,114],"parent-chain walk per workstream is O(n*depth) with a fresh `visited` set each time")]),
("scripts/baremetal-runner-report.py::render_table",[
 S("a",[143,152,166],"`a['runs']` is a set of run ids that holds exactly the keys of `a['run_totals']`; it is updated per record and only its length is read"),
]),
("scripts/baremetal-runner-report.py::collect_jobs",[
 S("a",[114,124,134],"`parse_iso(started)` is evaluated up to three times per job and `parse_iso(run_started_at)` once per job although it is constant per run"),
 S("b",[92,93,94],"jobs are fetched sequentially for every completed run; one subprocess `gh api` per run")]),
("scripts/gc-elections/create-github-comments.py::sync",[
 S("a",[145,146,147],"`remove_handle_line` is called once per stale handle, each call compiling a regex and rescanning the whole comment body; a single pass over the body with all stale handles would do"),
 S("b",[136,145,157],"`extract_mentions` is run on the same comment body up to three times (tagging pass, stale pass, post-removal check); the first two regex scans of each body are identical")]),
("scripts/gc-elections/create-github-comments.py::is_voter_comment",[
 S("a",[99,100,101,102],"`body.splitlines()` materialises every line of every comment on the issue just to compare the first line with HEADER; `HEADER not in body` rules out non-voter comments without splitting")]),
("scripts/gc-elections/create-github-comments.py::remove_handle_line",[
 S("a",[110,111,112,113,114],"regex is compiled from the escaped handle on each call")]),
("scripts/move-to-emeritus.py::_get_repo_commenters",[
 S("a",[255,256,257],"`number not in commenters[user][kind]` is a linear scan of a list per comment, quadratic for a user with many distinct issue/PR numbers")]),
("scripts/move-to-emeritus.py::_add_to_emeritus",[
 S("a",[859,871,872,873,874,875],"every line of the section is matched against `^[-*+] \\[` twice: once to collect `member_lines` and again in the loop that finds first/last member index"),
 S("b",[848,849,863,864],"regexes built per call / per sort key")]),
("scripts/move-to-emeritus.py::create_emeritus_prs",[
 S("a",[1198,1206,1210,1223,1230],"per user, `_find_section` and `_parse_members` rescan the whole README section for each role, and `_remove_member_line` and `_add_to_emeritus` rescan it again")]),
("scripts/move-to-emeritus.py::check_maintainer_activity",[
 S("a",[612,613,621,622],"expensive REST/GraphQL review verification (step 3) runs before the cheap authored-PR GraphQL count (step 4) for users who would be found active in step 4"),
 S("b",[595,604],"`_check_comments` is called twice over the same cached commenters (pr, then issue)")]),
("scripts/move-to-emeritus.py::_check_events",[
 S("a",[343,344,345,346,347,348,349],"iterates all cached events after every user in `remaining` has been found")]),
("scripts/update-sig-tables.py::render_group",[
 S("a",[157],"`extract_row_data(ws)` builds all ten fields, including the whole people loop with `person_link` calls, but render_group reads only meeting_schedule, calendar and slack_channels"),
 S("b",[159],"`content +=` accumulation of the table rows")]),
("scripts/update-sig-tables.py::render_sig_details",[
 S("a",[166],"`extract_row_data(ws)` is recomputed for every SIG here after `render_group` already computed it for the same ws")]),
("scripts/gc-elections/generate-voters-roll.py::build_devstats_rows",[
 S("a",[85,86,87,88,89,90,91,92,93,94,95,96,97,98],"one `requests.get` per devstats name inside `get_github_login`, with no Session, so every lookup pays a new TCP/TLS connection")]),
]
with open("step1.jsonl","w") as f:
    for u,s in recs: f.write(json.dumps({"step":1,"unit":u,"suspicions":s})+"\n")
