import json
O=lambda l,o,s=None,w=None:{"label":l,"outcome":o,"submission":s,"why":w}
B=lambda w:O("a","blocked",None,w)
recs=[
("scripts/validate-workstreams.py::validate_workstreams_semantics",[O("a","submitted","validate-team-sets"),O("b","submitted","validate-dead-parent-kind")]),
("scripts/baremetal-runner-report.py::render_table",[O("a","submitted","render-table-runs-set")]),
("scripts/baremetal-runner-report.py::collect_jobs",[B("inputs.py: it cannot run here: `collect_jobs` fetches GitHub Actions workflow runs and jobs via `gh_paginated`, which shells out to the `gh api` CLI to query github.com — it needs network access and subprocesses, both unavailable here")]),
("scripts/gc-elections/create-github-comments.py::sync",[O("a","submitted","sync-single-pass-removal"),O("b","submitted","sync-mentions-once")]),
("scripts/gc-elections/create-github-comments.py::is_voter_comment",[O("a","submitted","voter-comment-header-prefilter")]),
("scripts/move-to-emeritus.py::_get_repo_commenters",[B("inputs.py: it cannot run here: `_get_repo_commenters` calls `request_with_retry(\"GET\", url)` which performs a live HTTP request to https://api.github.com; no input can avoid it")]),
("scripts/move-to-emeritus.py::_add_to_emeritus",[O("a","submitted","emeritus-single-match-pass")]),
("scripts/update-sig-tables.py::render_group",[O("a","submitted","render-group-skip-people")]),
("scripts/gc-elections/generate-voters-roll.py::build_devstats_rows",[B("inputs.py: it cannot run here: `build_devstats_rows` calls `get_github_login` for every name, which issues `requests.get` to https://api.github.com/users/{username}; it needs live network access to GitHub")]),
]
with open("step3.jsonl","w") as f:
    for u,o in recs: f.write(json.dumps({"step":3,"unit":u,"outcomes":o})+"\n")
