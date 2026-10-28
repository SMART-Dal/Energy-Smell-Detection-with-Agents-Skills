Let me analyze the function under test: `render_group(group_name, sigs)`.

It iterates over `sigs` (list of dicts). Each `ws` needs `"name"`, `"resources"`, `"people"`, possibly `"tcSponsorship"`.

It calls `extract_row_data(ws)` which uses `ws.get("resources", [])` and `ws.get("people", [])`, and `ws.get("tcSponsorship")`.

Also `repository_link` and `roadmap_project_link` and `person_link` are used inside extract_row_data. These are defined in the module. Let me think — they likely read from some data. `person_link` maybe looks up a people mapping. `repository_link` probably formats a URL from repository dict. `roadmap_project_link` formats from project id and name.

We need to import the module. But wait — the module has module-level code that reads `readme_file`. Let's check: at module level there's

```python
with open(readme_file, encoding="utf-8") as f:
    content = f.read()
```

Hmm, that's in the "Definitions it uses from the same module" snippet. Actually the snippet shows it after `join_details`. That's module-level code that reads `readme_file`. If `readme_file` isn't defined or the file doesn't exist, importing the module will fail.

Also `subprocess` and `sys` are imported — module might run git commands at import. Actually the module-level code shown might be part of a function. The snippet "Definitions it uses from the same module" lists functions and then some module-level code `with open(readme_file...)`. Hmm, this could be inside `render_sigs_markdown`. Hard to say.

Actually the task says "Everything else its module defines (headers only)" lists functions, then separately there's module-level code. The `with open(readme_file...)` at module level would run on import. If `readme_file` is defined earlier in the module (maybe as `readme_file = "README.md"`), and README.md doesn't exist in cwd, import fails.

This is risky. We can't control import easily. But we could create the file? No—the module is in scripts/, and import would be from... Let me think about how the import works: `importlib.import_module('update-sig-tables')`. That requires the scripts directory to be on sys.path. Hmm. The task says to import exactly as shown. So presumably the harness adds scripts/ to sys.path.

But then module-level `open(readme_file)` would need the file. If readme_file is "README.md" relative path, and cwd is the repo root... maybe it exists.

Hmm, but we don't know. Let me think: maybe the module-level code shown is actually inside `render_sigs_markdown` function and got flattened in the description. The header `def render_sigs_markdown():` is listed but not its body. Then the `with open(...)` block appears — likely the body of `render_sigs_markdown`. That makes sense: `render_sigs_markdown()` reads the readme file. So it's NOT module-level. Good.

So importing should be fine. But there could be other module-level code like `sigs_file = "sigs.md"`, `readme_file = "README.md"`. Those are fine.

Wait, but the module also does `import subprocess`, `import sys`, `import yaml`. yaml may not be available? The task says use only packages the repository already imports. yaml is imported by the module, so presumably available.

Now, what does `person_link` do? Probably looks up a mapping from username to GitHub profile link, maybe reads a file. Let me guess. `repository_link(repository)` — probably builds a link from repository dict `{"name":..., "url":...}` or similar. `roadmap_project_link(project_id, name)` — builds link.

Since we can't know exactly, we should build `ws` dicts that exercise the paths. But we must ensure no exceptions. The risk: `person_link` might read from a global dict that's loaded from a file. If empty, it may return None, and code handles `person_link(...) or entry["gcLiaison"]`.

Hmm. Let's look at the resources handling:
- res with "meeting": m = res["meeting"]; schedule = m.get("schedule",""); gdoc = m.get("gDocNotes"); cal = m.get("calendarInviteGroup").
- res with "slack": s = res["slack"]; s['name'], s['id'].
- res with "githubDiscussion".
- res with "repository": repository_link(res["repository"]).
- res with "roadmapProject": roadmap_project_link(res["roadmapProject"], ws["name"]).

people entries: "gcLiaison", "tcSponsor" (dict with username, level), "specSponsor".

So we can construct realistic ws dicts.

But the concern is repository_link and roadmap_project_link might need certain structures. Let's guess:

```python
def repository_link(repository):
    return f"[{repository['name']}]({repository['url']})"
```

Hmm, uncertain. Maybe it uses `repository["org"]` and `repository["name"]`. If our input lacks a key, KeyError.

This is a real risk. Since we don't have the repo code, we need to be careful. But the task says "build the inputs from the classes and functions shown there." We only have headers for these helper functions.

Hmm, this is tricky. Let me think about the OpenTelemetry community repo `scripts/update-sig-tables.py`. I might recall it. Let me try.

Actually I recall the OpenTelemetry community repo has `scripts/update-sig-tables.py` and a `sigs.yml`. The sigs data comes from `sigs.yml`. Each SIG entry has `name`, `resources`, `people`, `tcSponsorship`.

Let me recall the structure of sigs.yml:

```yaml
- name: Specification SIG
  ...
```

Hmm. Let me think about the actual helper functions. From memory of the repo:

```python
def person_link(username):
    return f"[{username}](https://github.com/{username})"
```

Maybe it checks against a list of people? Actually there might be a `people.md` or similar.

Hmm, I think in that repo:

```python
def person_link(username):
    return f"[@{username}](https://github.com/{username})"
```

Not sure.

`repository_link`:
```python
def repository_link(repository):
    org = repository["org"]
    name = repository["name"]
    return f"[{org}/{name}](https://github.com/{org}/{name})"
```

Hmm.

`roadmap_project_link(project_id, name)`:
```python
def roadmap_project_link(project_id, name):
    return f"[{name}](https://github.com/orgs/open-telemetry/projects/{project_id})"
```

These are guesses. The risk of KeyError is real.

Alternative approach: avoid the risky branches entirely. We could build `ws` dicts with only "meeting", "slack", "githubDiscussion" resources and people with "gcLiaison", "tcSponsor", "specSponsor". But `repository_link` and `roadmap_project_link` are risky branches; we can avoid them by not including "repository" or "roadmapProject" resources. Similarly, person_link is used but code handles None.

Actually person_link is called for gcLiaison, tcSponsor, specSponsor. If person_link raises, that's a problem. But it's probably safe (just formats a link).

Hmm, but the task wants diverse, stressful inputs exercising different paths. But safety first. We can include repository and roadmapProject but risk KeyError.

Let me think harder about the actual repo. The task description says "Everything else its module defines (headers only)" - so the graders know we can't see bodies. They expect us to build inputs that work. So probably these helpers are tolerant.

Let me try to recall the actual file. Searching memory: "update-sig-tables.py" opentelemetry community.

I believe the sigs data structure in `sigs.yml` looks like:

```yaml
- name: Specification SIG
  resources:
    - meeting:
        schedule: "..."
        gDocNotes: "..."
        calendarInviteGroup: "..."
    - slack:
        name: "..."
        id: "..."
    - githubDiscussion: "..."
  people:
    - gcLiaison: username
    - tcSponsor:
        username: ...
        level: ...
  tcSponsorship: collective
```

And there's a `repositories` list maybe. Hmm.

Actually I recall the helper functions might be like:

```python
def repository_link(repository):
    return f"[{repository}](https://github.com/{repository})"
```

If repository is a string.

Given the uncertainty, I'll design inputs that avoid the two riskiest branches (repository, roadmapProject), OR include them but... hmm.

Actually, wait. Let me reconsider: the note in extract_row_data:
```python
repositories.append(repository_link(res["repository"]))
roadmap_projects.append(roadmap_project_link(res["roadmapProject"], ws["name"]))
```

`res["repository"]` and `res["roadmapProject"]` — these are passed. If repository_link expects a dict, res["repository"] is a dict.

Given the repo's README likely has repository links like "[open-telemetry/opentelemetry-specification](https://github.com/open-telemetry/opentelemetry-specification)". Hmm.

Let me try to find actual code. I think the community repo's `sigs.yml` entries look like:

```yaml
- name: 'Specification SIG'
  resources:
    - meeting:
        schedule: 'Weekly, Tuesdays at 08:00 PT'
        gDocNotes: '...'
    - slack:
        name: '#otel-specification'
        id: 'C01...'
  people:
    - gcLiaison: ...
```

I'm not confident about repository format.

Safest: skip "repository" and "roadmapProject" resources. The measured function still does substantial work with many sigs and many resources. Actually the task says "different paths through its code". Hmm, but a KeyError would break everything.

Alternatively, we could probe by... no, we can't run.

Let me weigh: The graders presumably wrote this task from the actual repo. They say "build the inputs from the classes and functions shown there." They show `repository_link(res["repository"])` and `roadmap_project_link(res["roadmapProject"], ws["name"])`. So the shape is known: repository is whatever res["repository"] is; roadmapProject is passed as first arg. We don't know inner structure.

I think a reasonable guess: repository is a dict with keys like "name" and "url"? Or maybe it's the full URL string?

Hmm. Let me think about what would make a nice link in the README. The README "Details" section for each SIG lists repositories. Actually let's think about the actual opentelemetry community README. I recall a table "SIGs and their meeting times" with columns Name, Meeting Time, Meeting Invites Group, Slack Channel, Details.

The details page `sigs.md` (or `sigs/<name>.md`) contains per-SIG details including repositories, roadmap projects.

Let me try to recall the sigs.yml format more concretely. I've seen:

```yaml
- name: Specification SIG
  resources:
    - meeting:
        schedule: "Weekly, Tuesdays at 08:00 PT"
        gDocNotes: "..."
        calendarInviteGroup: "otel-specification"
    - slack:
        name: "#otel-specification"
        id: "C01..."
    - githubDiscussion: "https://github.com/open-telemetry/community/discussions/..."
    - repository: "open-telemetry/opentelemetry-specification"
    - roadmapProject: "specification"
```

Hmm, if repository is a string like "open-telemetry/opentelemetry-specification", then repository_link would be:

```python
def repository_link(repository):
    return f"[{repository}](https://github.com/{repository})"
```

And roadmapProject might be a project number or name, with name being the SIG name.

Honestly, I'll take a pragmatic approach: I'll include repository and roadmapProject resources with string values, and hope. Actually no — if it's wrong, all cases fail.

Hmm, let me reconsider. Is there a way to make the function robust? No.

Alternative: I could avoid those branches. The task requires 8 diverse cases and 4 will be kept. Even without repository/roadmap branches, we have meeting/slack/githubDiscussion and people branches. That's enough diversity.

But we lose potential work. Well, the main work is string concatenation over many sigs.

Actually, let me reconsider the risk differently: maybe I should include them but guard by... no, can't guard.

Decision: I'll include "repository" and "roadmapProject" in some cases only if I'm reasonably confident. Let me try to actually recall the repo code. 

I'm now fairly sure about the opentelemetry community repo. Let me think about `scripts/update-sig-tables.py`. I believe it's a newer script (2024) that generates the README table from `sigs.yml`.

Let me try recalling `repository_link`:

```python
def repository_link(repository):
    return f"[{repository['org']}/{repository['repo']}](https://github.com/{repository['org']}/{repository['repo']})"
```

Hmm.

Or maybe:

```python
def repository_link(repository):
    org, repo = repository.split("/")
    return f"[{repository}](https://github.com/{repository})"
```

If I pass a string "open-telemetry/opentelemetry-specification", the first version fails (string indexing with 'org'). The second version works with string.

If I pass a dict {"org":..., "repo":...}, the second fails.

50/50.

Hmm, what about roadmap_project_link(project_id, name)? If project_id is a number, and it builds a link to github projects. Passing a string might work.

I think the safest is to omit both. Let me just do that. The remaining branches give good coverage.

Actually wait — but the grader compares outputs of original vs modified function. We just need inputs that run on the original. If repository_link is simple and works with strings, including it adds value. But risk of total failure is high.

Let me reconsider once more. Is there any chance the module import itself fails? The module imports `yaml`. And has module-level code. If module-level `readme_file` open... we decided it's inside render_sigs_markdown. Actually let me reconsider: the snippet order:

```python
def join_details(values):
    return ", ".join(value for value in values if value)

with open(readme_file, encoding="utf-8") as f:
    content = f.read()
```

This is presented right after join_details, in the "Definitions it uses from the same module" section. If it were module-level, it'd be weird to show it here. But it might genuinely be module-level in the actual file (the file may have top-level code). Hmm.

Actually, in these task descriptions, the "Definitions it uses from the same module" section shows the functions the target function depends on, and then maybe some module-level statements that are executed. The `with open(readme_file...)` could be module-level code that runs at import. If so, importing would execute it and possibly fail.

But the task says "Import it as importlib.import_module('update-sig-tables').render_group" — they expect the import to work. So presumably module-level code is safe (or the harness handles it). Hmm, but we might need to provide readme_file.

Given the module-level snippet uses `readme_file`, and the module likely defines `readme_file = "README.md"`. If cwd is repo root, README.md exists. Fine.

Hmm, but if import fails, we can't do anything. Let's assume it works.

Actually, let me reconsider: maybe `readme_file` is defined in the module and the top-level code reads it. Let me look at the listed module defines: the "Everything else its module defines (headers only)" lists functions only, no variables. But `sigs_file = "sigs.md"` is given. So variables exist. `readme_file` probably = "README.md".

OK. Let me now design.

I'll write the input generation:

```python
import random

def _ws(name, rng, kind):
    ws = {"name": name}
    resources = []
    people = []
    ...
    return ws
```

Let me build sigs with many resources to make it heavy.

Since extract_row_data is O(resources + people), and render_group is O(sigs), we can make many sigs each with many resources.

Workload target: 1ms-200ms per call. String building over say 2000 sigs with 20 resources each = 40000 iterations, each doing string ops. Probably a few ms. Let's make it bigger: 5000 sigs.

But output must be under 100000 values. The output is a string; "values" probably means length? "keep what it returns ... under about 100 000 values". A string of 100000 chars might be ok. Let's keep the content moderate. Actually the returned content is a markdown string; each row maybe 300 chars. 5000 rows → 1.5M chars. That's over 100k. Hmm, "values" is ambiguous but likely counts the string length or list elements. To be safe, keep rows moderate.

Hmm, "Its arguments are rendered before and after each call" — arguments rendered means repr of the args. The sigs list of 5000 dicts with 20 resources each would be huge in repr — way over 1,000,000 values. So keep the input under 1e6 values.

Let's be careful. Each ws dict: name + resources list + people list. Say 10 resources each with ~3 keys → ~30 values, plus people ~3 entries. So ~40 values per ws. 5000 ws → 200,000 values. Under 1e6. OK.

Output: content string. Length ~ rows * 250 chars. 5000 rows → 1.25M chars. Hmm, that's a single string though. "under about 100 000 values" — I'll interpret values as elements; a string is one value. But to be safe, maybe keep output under ~100k chars too. Let's target ~2000-3000 sigs.

Actually, let's think about the time: each row does several f-strings and joins. For 3000 rows, maybe 1-3 ms. We want ~1ms-200ms. Let's aim for the larger side: make each ws have more resources so extract_row_data does more work. E.g., 30 resources per ws, 2000 ws → 60000 resource iterations. That's decent.

Hmm, but we want diverse cases. Let's define a builder with parameters.

Let me design 8 cases:
1. Many small sigs (e.g., 5000 sigs, 2 resources each) — tests iteration overhead.
2. Few large sigs (e.g., 50 sigs, 500 resources each) — tests extract_row_data depth.
3. Mixed with meeting/slack/githubDiscussion.
4. All slack channels (many slack channels per sig).
5. Many people entries.
6. tcSponsorship collective.
7. Long names / unicode / special chars for heading_anchor.
8. All resources types combined, big.

Avoid repository/roadmap. Hmm, but that reduces diversity. Let me reconsider including them.

Actually, you know what, let me try to recall the actual repository_link. I'll search memory for "opentelemetry community update-sig-tables".

I have a vague memory that sigs.yml entries have resources like:

```yaml
resources:
  - meeting:
      schedule: ...
      gDocNotes: ...
      calendarInviteGroup: ...
  - slack:
      name: ...
      id: ...
  - githubDiscussion: ...
  - repository:
      name: opentelemetry-specification
      org: open-telemetry
  - roadmapProject: ...
```

Hmm.

Actually, thinking about it more: the README details for each SIG include "Repositories" and "Roadmap Projects". The roadmap project link probably: `https://github.com/orgs/open-telemetry/projects/<id>`.

I really can't be sure. I'll omit them to be safe. Actually — hold on. Let me reconsider: maybe I can include them in checks() (not measured) — no, checks are for edge behavior, and if they raise that's OK for checks! "checks(): 2 or 3 small edge inputs checked only for identical behaviour, never measured. These may raise."

Oh interesting. So I could put risky branches in checks()! If they raise, that's fine (both original and modified raise identically? well, the modified version should also raise). Hmm, but if the modified version is a refactor, it might raise differently. Risky. Actually checks compare behavior; if both raise, it's probably fine.

But better: I can use checks to probe... no, I can't see the output.

Hmm, but actually I could put a case that includes repository/roadmapProject in checks, and if it works, great. But it doesn't help the measured cases.

Let me just try to include repository and roadmapProject with a dict/string that's likely. Ugh.

Alternative clever approach: Since we can't know, maybe include them and hope the helper handles gracefully. Actually — many such helper functions might do `repository.get(...)` or format directly.

Hmm, let me think about what's most likely given the code style. The module uses f-strings heavily, walrus operators. The helper:

```python
def repository_link(repository):
    return f"[{repository}](https://github.com/{repository})"
```

This is plausible if repository is "org/repo".

For roadmap_project_link(project_id, name):
```python
def roadmap_project_link(project_id, name):
    return f"[{name}](https://github.com/orgs/open-telemetry/projects/{project_id})"
```

plausible if project_id is a number.

Hmm, but then why pass name? Because the link text is the SIG name. Yes! That makes sense: roadmap project link shows the SIG name as the link text.

And repository_link just takes the repository. If it's "org/repo" string, link text is "org/repo".

Actually, I now think this is quite plausible. Let me look at the README of opentelemetry community... The details section for SIGs lists "Repository: [open-telemetry/opentelemetry-specification](https://github.com/open-telemetry/opentelemetry-specification)".

Hmm OK. But there's still risk.

Let me think about the people: `person_link(entry["gcLiaison"]) or entry["gcLiaison"]`. If person_link returns a link for known users and None for unknown. That suggests person_link looks up a mapping of GitHub usernames to real names, maybe from a file like `people.yml` or the README. Hmm! If person_link reads a file that doesn't exist... it might raise.

Hmm, that's a concern. `person_link(username)` probably:

```python
def person_link(username):
    return f"[{username}](https://github.com/{username})"
```

But then it never returns None, and `or entry["gcLiaison"]` is redundant. So person_link probably returns None sometimes, meaning it looks up a mapping. Maybe it reads a `people.yml` or a `.github/...` file.

Actually maybe person_link reads from a global dict loaded from `people.md`. Hmm.

Wait, maybe it uses the `content` variable (the README content read at module level)? Like searching the README for the person's name? That would explain the module-level `content = f.read()`.

Hmm! That's interesting. `person_link` might search the README content for a username and return a link with their name. If so, our test needs README content. But if content is empty or doesn't contain, returns None, and code falls back to username. Fine.

Actually wait, re-reading: the `with open(readme_file...)` is shown right after join_details, and `readme_file` isn't in the headers list. This strongly suggests it's module-level code (since if it were inside render_sigs_markdown, the body would just not be shown). Actually the description shows "Everything else its module defines (headers only)" then the with-open block. Hmm, the with-open block might be top-level.

If it's top-level and `readme_file` is defined as e.g. `readme_file = "README.md"`, then import requires README.md in cwd. The harness probably runs from repo root. Should be fine.

OK, I'll go with person_link being safe.

Let me now decide: include repository and roadmapProject? I'll include them, guessing repository is a string "org/repo" and roadmapProject is a project number (string or int). Hmm, but if wrong → KeyError → all cases fail.

Risk assessment: If I omit them, I lose some coverage but everything runs. If I include and guess wrong, I fail entirely. Given "simple inputs that run are better than clever ones that do not", I'll omit them.

Hmm, but wait — actually, maybe I can include them in only ONE case, so if that case fails, the others still... no! Every case must run to completion on the original. If one raises, the whole thing fails? The instruction: "Every case must run to completion on the original function without raising." So all 8 must run. Can't risk it.

OK, omit repository and roadmapProject.

Hmm, but actually let me reconsider. Let me think about whether I can find the actual code. The repo is "community" (open-telemetry/community). Let me try hard to recall.

I believe the file is at `scripts/update-sig-tables.py` and the data at `sigs.yml`. Hmm, actually maybe `sigs.yml` doesn't exist; maybe it's in the README.

Honestly, without certainty, omit.

Wait, actually — maybe I should reconsider: the task explicitly shows `repository_link(res["repository"])` and `roadmap_project_link(res["roadmapProject"], ws["name"])` in the function body. The task author expects us to feed these. But they also said build from what's shown. The shown info doesn't give inner structure. So maybe the author expects us to just feed plausible data.

Hmm, hmm. Let me think about which is more likely to be "correct" for the actual repo.

Let me try recalling sigs.yml from opentelemetry community... I think there is a file `sigs.yml` with entries like:

```yaml
- name: Android SIG
  ...
```

Hmm no.

Alternatively, the data might come from the README itself parsed.

Actually, you know, let me reconsider: maybe the "resources" entries' repository is a URL string. Like `- repository: https://github.com/open-telemetry/opentelemetry-specification`. Then repository_link might be:

```python
def repository_link(repository):
    return f"[{repository}]({repository})"
```

Hmm.

I'll go with omitting. Let me maximize other diversity.

Actually, wait. Let me reconsider including repository as a string "open-telemetry/opentelemetry-specification". Two plausible implementations:
- `f"[{repository}](https://github.com/{repository})"` → works with string.
- dict access → fails.

And roadmapProject as int/string. Two plausible:
- `f"[{name}](https://github.com/orgs/open-telemetry/projects/{project_id})"` → works.
- dict access → fails.

Probability maybe 50%. Not worth it for the whole task.

Hmm, but actually, consider: `roadmap_project_link(project_id, name)`. If roadmapProject were a dict, they'd probably pass the dict and access name inside. Passing `ws["name"]` separately suggests project_id is a scalar (number) and name is the link text. So scalar is likely! Similarly `repository_link(res["repository"])` — single arg, could be string or dict.

So roadmapProject is likely a scalar (project number). I could include roadmapProject with an int. Risk lower. But still repository.

Meh. Let me just include both as scalars and hope. Hmm, no. Let me think about consequences: if I'm wrong, the entire submission fails → score 0. If I omit, I get a decent score. Expected value favors omitting.

Hmm, but the task also says the 4 cases that do the most work are kept. If all my cases are similar work, fine.

Decision: omit repository and roadmapProject. Use meeting, slack, githubDiscussion, and people.

Hmm, wait. Actually, let me reconsider one more time by thinking about the real file. Let me try to recall the OpenTelemetry community README table:

| Name | Meeting Time | Meeting Invites Group | Slack Channel | Details |

And the sigs details page has sections like:

### Specification SIG
**Meeting Time:** ...
**Meeting Invites Group:** ...
**Slack Channels:** ...
**GitHub Discussions:** ...
**Repositories:** ...
**Roadmap Projects:** ...
**GC Liaisons:** ...
**TC Sponsors:** ...
**Spec Sponsors:** ...

Yeah.

I found in memory: opentelemetry community has `sigs.yml`? Hmm. Actually I think the file is `sigs.yml` at repo root? Or the script reads `README.md` and extracts. Actually the script `update-sig-tables.py` probably reads `sigs.yml`.

Hmm, honestly I recall a `sigs.yml` in open-telemetry/community. Let me try to recall its structure:

```yaml
- name: Specification SIG
  resources:
    - meeting:
        schedule: "Weekly, Tuesdays at 08:00 PT"
        gDocNotes: "..."
        calendarInviteGroup: "otel-specification"
    - slack:
        name: "#otel-specification"
        id: "C0123456789"
    - repository: "open-telemetry/opentelemetry-specification"
    - roadmapProject: 42
  people:
    - gcLiaison: "someone"
```

Hmm, plausible.

OK here's another thought: I could include repository/roadmapProject in a check() case (not measured). If it raises, fine. If it doesn't, no info gained but no harm. Actually the check comparison: original vs modified — both should behave identically. If original raises KeyError and modified raises KeyError, likely fine. So including risky branches in checks is safe-ish. But it doesn't help measured cases.

Let me include one check with repository+roadmap to at least exercise it, and hope. Actually no, checks that raise are fine but "may raise" — but if the modified version doesn't raise, mismatch. Eh, still fine, it's just a check.

Hmm, actually let me not overthink. I'll include repository and roadmapProject in checks() only.

Hmm, but actually — if the helper functions require reading a file that doesn't exist, calling them in checks raises. Fine.

OK now let me write the code.

```python
import random

def _make_ws(name, rng, n_meeting=1, n_slack=1, n_disc=1, n_people=1, collective=False, long_name=False):
    resources = []
    for i in range(n_meeting):
        m = {"schedule": f"Weekly, day {rng.randrange(7)} at {rng.randrange(24):02d}:00 PT"}
        if rng.random() < 0.8:
            m["gDocNotes"] = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789-_") for _ in range(44))
        if rng.random() < 0.6:
            m["calendarInviteGroup"] = f"otel-{name.lower().replace(' ', '-')}"
        resources.append({"meeting": m})
    ...
```

Wait, careful: extract_row_data only handles the FIRST meeting (it overwrites meeting_schedule each time? no, it sets meeting_schedule = m.get(...) each time, so last one wins). Actually it loops and for each "meeting" res overwrites. Fine.

Also note: multiple slack resources accumulate.

Let's write a generator with a spec.

Let me define:

```python
def _sig(rng, idx, kind):
    name = f"SIG-{idx} ..."
```

Let me think about heading_anchor: it strips non [a-z0-9\s-] chars. Names with special chars exercise it. But name goes into the row and the anchor.

Let me now write cases.

Case A: "many-sigs-few-resources": 4000 sigs, each 1 meeting + 1 slack + 1 discussion, 2 people.

That's 4000 * (extract_row_data over ~3 resources + 2 people). Output 4000 rows. Content length maybe 4000*200 = 800k chars. Hmm, "values" — if it counts string length, that's over 100k. Risky.

Hmm, the constraint "keep what it returns (and anything it writes) under about 100 000 values". A returned string of 800k chars — is that 800k values? Probably they mean elements of collections. But to be safe, maybe keep output under ~100k chars? That would limit to ~400 rows. But then work per call is small (~0.2ms). Hmm.

Actually let's reconsider: "Its arguments are rendered before and after each call to see whether it changed them, so keep each input's data under about 1 000 000 values." So rendering the args (a list of dicts) — they count all nested values. For output, "keep what it returns under about 100 000 values" — for a string, values might be characters? Or they might just not care for strings.

To be safe, let's keep output under 100k chars. Hmm, but then each call is fast. We need ~1ms+. 100k chars of output... building it takes maybe 1ms? Let's estimate: 400 rows, each row ~250 chars, building via f-strings ~ maybe 0.3ms. Hmm.

Actually, we can make the work heavy without making output huge by having many resources per sig (extract_row_data does work) but few sigs. E.g., 200 sigs each with 200 resources → 40000 resource iterations, output 200 rows → 50k chars. That's good: heavy extract_row_data, small output.

Wait but extract_row_data only extracts meeting/slack/discussion/repo/roadmap. Multiple slack → many slack channels → join_details produces long strings → output grows. Multiple discussions → discussions list. But discussions aren't in the row! Let's check render_group row: `{name}`, `{data['meeting_schedule']}`, `{data['calendar']}`, `{join_details(data['slack_channels'])}`, details. So discussions, repositories, roadmap_projects, gc_liaisons, tc_sponsors, spec_sponsors are NOT in the row (they're used in render_sig_details). But extract_row_data still computes them! So we can add many repositories/roadmap/discussions/people to make extract_row_data work hard without growing the output.

That's the key insight: put many people entries and discussions → heavy work, no output growth. 

So: sigs with many people (gcLiaison, tcSponsor, specSponsor) and many discussions → extract_row_data does lots of string formatting but the row stays short.

But person_link is called for each person — if person_link is expensive or risky... Let's assume it's cheap and safe.

Hmm, but person_link might read a file each call? Unlikely.

OK so design cases:

1. many-sigs: 3000 sigs, minimal resources (1 meeting, 1 slack), 1 person. Output ~3000 rows * ~180 chars = 540k chars. Hmm still large.

Let me reduce to keep output < 100k chars: ~400 rows. Or accept larger. Ugh.

Let me reconsider the "100 000 values" limit. I think for a string, they'd count it as one value or measure length. Given ambiguity, I'll keep outputs under ~100k characters to be safe. Actually, hmm, but that severely limits.

Hmm, let me re-read: "The function's output is compared in full after every input, so keep what it returns (and anything it writes) under about 100 000 values."

I think "values" here means elements/characters. Comparing a 500k-char string is fine computationally. But the limit is about memory/comparison cost. I'll aim for ~100k chars max, maybe slightly over is fine ("about").

Let's target outputs of 30k-90k chars.

With ~150 chars per row, that's 200-600 sigs. Hmm, work per call then is small. To reach 1ms, we need more per-sig work. So use many resources/people per sig.

Plan: 
- Case 1: 500 sigs, 1 meeting + 1 slack each, 5 people each (mostly tcSponsor with levels). Output 500 rows ~ 90k chars. Work: 500*6 resource/person iterations. Maybe 0.5ms. Hmm.

We need ~1ms. Let's add more people: 50 people per sig → 500*50 = 25000 person_link calls + string ops. That's probably several ms. And output stays small.

But wait, people with gcLiaison/tcSponsor/specSponsor → person_link(username). If person_link does a dict lookup, cheap. 25000 calls → maybe 2-5ms. Good.

Hmm, but is that "realistic"? The task says realistic data. Real SIGs have a handful of people. But "stressful" inputs are also wanted. 50 people per sig is unrealistic but stressful. The task says "Use realistic scale and complexity" but also "Generate stressful inputs". I think making it heavy is fine.

Actually, let me reconsider: "Define a real workload: the kind of data this function gets in this repository". Real sigs count is maybe 40. Each with a few resources. So real workload is small (40 rows). One call would be << 1ms. But they want 1ms-200ms. So we must scale up. That's expected ("stressful").

I'll scale: hundreds of sigs, each with many resources/people.

Let me now think about which paths to exercise:
- meeting with gDocNotes and calendarInviteGroup (calendar).
- meeting without gDocNotes/calendar.
- slack channels (multiple).
- githubDiscussion (multiple).
- people: gcLiaison, tcSponsor with level, tcSponsor without level, tcSponsor level "tbd", specSponsor.
- tcSponsorship == "collective".

Let's write the generator.

```python
import random

_LOREM = "OpenTelemetry SIG working group"

def _person(rng, kind):
    user = f"user{rng.randrange(100000)}"
    if kind == "gc":
        return {"gcLiaison": user}
    if kind == "spec":
        return {"specSponsor": user}
    # tc
    sponsor = {"username": user}
    r = rng.random()
    if r < 0.5:
        sponsor["level"] = rng.choice(["collector", "contributor", "tbd"])
    return {"tcSponsor": sponsor}
```

Wait, careful: "gcLiaison" key must be in entry. The code checks `if "gcLiaison" in entry`. Good.

Now build resources:

```python
def _resources(rng, n_meeting, n_slack, n_disc, name):
    res = []
    for i in range(n_meeting):
        m = {"schedule": ...}
        ...
```

Let me just write it.

Note about `sigs_file` global: used in the details link: `f"[Details](./{sigs_file}#{heading_anchor(name)})"`. sigs_file = "sigs.md" already set in module. Fine.

Now, is there any module-level global that needs setting? `sigs_file` is already defined. `readme_file` maybe. Not needed.

Now write the thunks. The function doesn't modify sigs, so we can reuse the same list across calls. Good — build once at module level.

But careful: extract_row_data reads ws.get(...). No mutation. render_group doesn't mutate. So safe to share.

Now let's write 8 cases with different shapes:

1. "wide-many-sigs": 400 sigs, each 1 meeting (with gdoc+cal), 1 slack, 1 discussion, 3 people. → tests many sigs.
2. "deep-many-resources": 60 sigs, each 100 slack + 100 discussion + 200 people. → tests resource loop depth. Output: 60 rows with 100 slack channels each → each slack channel string ~60 chars → join ~6000 chars per row → 60*6000 = 360k chars. Too big!

Hmm, slack channels appear in output. So many slack channels → big output. Keep slack count low.

So for heavy work without output, use discussions and people (not in output). And repositories/roadmap (not in output) — but those are risky. So use discussions + people.

2. "many-discussions-people": 100 sigs, each 500 discussions + 300 people, 1 meeting, 1 slack. Output: 100 rows * ~150 chars = 15k chars. Work: 100*800 = 80000 iterations. Good, heavy.

Hmm, but discussions: `discussions.append(f"[GitHub Discussions]({res['githubDiscussion']})")`. Fine.

3. "people-heavy": 300 sigs, 100 people each. Work 30000 person calls.
4. "slack-heavy-but-small-output": 200 sigs, 3 slack each. Output 200 rows, slack join ~ 3*60=180 chars → row ~300 chars → 60k chars. OK.
5. "collective-tc": sigs with tcSponsorship collective (resets tc_sponsors).
6. "meeting-variants": some with gDocNotes, some with calendarInviteGroup, some neither.
7. "long-names-special-chars": names with brackets, markdown links, unicode, to exercise heading_anchor.
8. "mixed-realistic-large": combination.

Let me also consider: heading_anchor does regex sub. Names with markdown links `[foo](bar)` and special chars. Good for case 7.

Let me now write code carefully.

```python
import random

def _meeting(rng, i):
    m = {"schedule": f"Weekly, {rng.choice(['Mon','Tue','Wed','Thu','Fri'])} at {rng.randrange(24):02d}:00 PT"}
    if rng.random() < 0.8:
        m["gDocNotes"] = "1" + "".join(rng.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_") for _ in range(43))
    if rng.random() < 0.7:
        m["calendarInviteGroup"] = f"otel-{rng.randrange(1000)}"
    return {"meeting": m}
```

etc.

Now the main builder:

```python
def _build_sigs(n_sigs, n_meeting, n_slack, n_disc, n_gc, n_tc, n_spec, seed, collective_ratio=0.0, name_fn=None):
    rng = random.Random(seed)
    sigs = []
    for i in range(n_sigs):
        name = name_fn(i, rng) if name_fn else f"SIG {i}"
        ws = {"name": name, "resources": [], "people": []}
        for j in range(n_meeting):
            ws["resources"].append(_meeting(rng, j))
        for j in range(n_slack):
            ws["resources"].append({"slack": {"name": f"#chan-{rng.randrange(1000)}", "id": f"C{rng.randrange(10**10):010d}"}})
        for j in range(n_disc):
            ws["resources"].append({"githubDiscussion": f"https://github.com/open-telemetry/community/discussions/{rng.randrange(10**4)}"})
        for j in range(n_gc):
            ws["people"].append({"gcLiaison": f"gc{j}-{rng.randrange(1000)}"})
        for j in range(n_tc):
            sp = {"username": f"tc{j}-{rng.randrange(1000)}"}
            if rng.random() < 0.5:
                sp["level"] = rng.choice(["collector", "contributor", "tbd"])
            ws["people"].append({"tcSponsor": sp})
        for j in range(n_spec):
            ws["people"].append({"specSponsor": f"spec{j}-{rng.randrange(1000)}"})
        if collective_ratio and rng.random() < collective_ratio:
            ws["tcSponsorship"] = "collective"
        sigs.append(ws)
    return sigs
```

Hmm, careful with person_link: usernames like "gc0-123" — person_link probably handles any string.

Now cases. Let me estimate output sizes.

Row format: `| {name} | {meeting_schedule} | {calendar} | {slack} | [Details](./sigs.md#{anchor}) |\n`

With name ~10, schedule ~25, calendar ~60 (link), slack ~60, details ~30 → ~190 chars per row.

So 500 rows → 95k chars. OK, cap n_sigs around 400-500 for output safety.

But heavy work needs many iterations. Use resources/people.

Let me define cases:

1. "many-sigs": 500 sigs, 1 meeting, 1 slack, 0 disc, 1 gc, 1 tc, 0 spec. Output ~500 rows*~180 = 90k. Work: 500*(3 resources + 2 people) = 2500 iterations. Probably ~1ms. Hmm, maybe less. Let's add more per sig? But output grows with sigs count only... no, output grows with sigs count, not resources. So adding resources per sig doesn't grow output (except slack/disc? disc not in output, slack in output). So add many disc + people per sig for work.

1. "many-sigs": 500 sigs, 1 meeting, 1 slack, 20 disc, 10 gc, 10 tc, 5 spec. Output 500 rows. Work: 500*(2+20+25)=23500 iterations. Good.

2. "deep-resources": 80 sigs, 5 meeting, 3 slack, 500 disc, 200 people. Output 80 rows * ~250 = 20k. Work 80*710 = 57000. Good.

3. "slack-heavy": 300 sigs, 1 meeting, 4 slack. Output 300*~250=75k. Work small though (300*5). Hmm, add people/disc for work: 30 disc, 20 people. 

4. "people-heavy": 200 sigs, 1 meeting, 1 slack, 300 people. Work 200*300=60000 person iterations.

5. "collective": 250 sigs, half collective. 

6. "meeting-variants": mix.

7. "special-names": 400 sigs with weird names.

8. "mixed-big": 400 sigs, all resource types.

Hmm, I worry about the person_link cost if it's not trivial. But fine.

Also concern: 500 disc per sig → 80*500=40000 f-string appends. Fine.

Let me also ensure the total input data < 1e6 values. Case 2: 80 sigs * (500 disc dicts + 200 people dicts + ...) = 80*710 = 56800 dicts, each ~2 values → ~150k values. Fine. Case 4: 200*300 = 60000 dicts. Fine. Case 3: 300*~50=15000. Fine.

Total across all cases: maybe 500k values. Each case separately is what matters (rendered per case). Fine.

Memory: fine.

Now checks():
- empty sigs: ("empty", lambda: ("Empty Group", []))
- single sig with no resources/people: ("minimal", lambda: ("X", [{"name": "X"}]))
- weird name / None-ish: ("weird-name", lambda: ("Y", [{"name": "[Foo](bar) !!", "resources": [], "people": []}]))

Wait, but `ws["name"]` is accessed — fine. And extract_row_data uses ws.get. So a dict with just "name" works.

Check for odd type: maybe sigs = None → would raise TypeError (iterating None). "may raise" — fine. Let's include ("none-sigs", lambda: ("G", None)). Both versions should raise TypeError identically. Hmm, modified version might handle differently. It's a check; risky but allowed. Actually, let me be careful: the modified version is a refactor, presumably same behavior. If original raises TypeError on None and modified raises TypeError, fine. I'll include it.

Hmm, actually if sigs=None, `for ws in sigs` raises TypeError. Fine.

Also include a check with repository/roadmapProject to exercise? If repository_link is fine, good; if not, raises — both versions raise. I'll include one in checks. Actually, if it raises in checks, is that a problem? "These may raise." So OK.

Hmm, but if original raises KeyError and modified raises KeyError with different message... comparison is on behavior. Probably just exception type. Fine. But let me not risk weirdness; I'll skip repository/roadmap entirely. Actually, let me include one check that uses repository and roadmapProject — it might work and add coverage; if it raises, it's allowed. Hmm, but a raise in checks means the check "passes" only if both raise. Since the modified is a refactor, both would raise the same. OK, include it.

Hmm, actually there's a subtlety: if the modified version is a *refactor* that handles things differently... The task is about energy measurement; modified version presumably computes same result. If original raises on our weird input, modified likely also raises. Fine.

I'll include it.

Now, one more concern: does `render_group` need `sigs_file`? It's module global = "sigs.md". Fine.

Let me write the final code.

Actually, let me reconsider the number of sigs to keep output under 100k. Let me compute more carefully with a typical row.

`| SIG 123 | Weekly, Tue at 08:00 PT | [otel-123](https://groups.google.com/a/opentelemetry.io/g/otel-123) | [#chan-123](https://cloud-native.slack.com/archives/C0123456789) | [Details](./sigs.md#sig-123) |\n`

Lengths: "| SIG 123 | " ~12, schedule ~24, " | " 3, calendar link ~75, " | " 3, slack link ~65, " | " 3, details ~30, " |\n" 3. Total ~218. Plus header ~150.

So 400 sigs → ~87k + header. OK. Let's use 400 sigs max for cases with full rows. For cases where calendar/slack are empty, rows are shorter.

Let me set:
- Case 1 "many-sigs": 400 sigs.
- Case 2 "deep": 100 sigs.
- Case 3 "slack-heavy": 250 sigs, 3 slack each → row ~350 → 87k. Hmm, 3 slack links = ~195 chars just slack. Row ~350. 250*350 = 87k. OK.
- Case 4 "people-heavy": 250 sigs.
- Case 5 "collective": 300 sigs.
- Case 6 "meeting-variants": 350 sigs.
- Case 7 "special-names": 300 sigs.
- Case 8 "mixed": 200 sigs with lots of resources.

Fine.

Now let me write it all out.

One more: `_meeting` uses rng.choice on list — fine.

For special names, include markdown links like `[Spec](https://x) SIG` and unicode and punctuation. heading_anchor: removes non [a-z0-9\s-] after lowercasing. Unicode chars removed. Fine.

Let me write.

```python
import random

def _meeting(rng):
    m = {
        "schedule": "Weekly, %s at %02d:00 PT" % (rng.choice(["Mon", "Tue", "Wed", "Thu", "Fri"]), rng.randrange(8, 20)),
    }
    if rng.random() < 0.8:
        m["gDocNotes"] = "1" + "".join(rng.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_") for _ in range(43))
    if rng.random() < 0.7:
        m["calendarInviteGroup"] = "otel-%d" % rng.randrange(1000)
    return {"meeting": m}
```

Wait, if gDocNotes present but calendar absent etc. Also sometimes a meeting res with neither.

Let me create a function to build a sig:

```python
def _sig(name, rng, n_meeting=1, n_slack=1, n_disc=0, n_gc=0, n_tc=0, n_spec=0, collective=False):
    ws = {"name": name, "resources": [], "people": []}
    for _ in range(n_meeting):
        ws["resources"].append(_meeting(rng))
    for _ in range(n_slack):
        ws["resources"].append({"slack": {"name": "#chan-%d" % rng.randrange(10000), "id": "C%010d" % rng.randrange(10**10)}})
    for _ in range(n_disc):
        ws["resources"].append({"githubDiscussion": "https://github.com/open-telemetry/community/discussions/%d" % rng.randrange(10000)})
    for _ in range(n_gc):
        ws["people"].append({"gcLiaison": "gc%d" % rng.randrange(100000)})
    for _ in range(n_tc):
        sp = {"username": "tc%d" % rng.randrange(100000)}
        if rng.random() < 0.6:
            sp["level"] = rng.choice(["collector", "contributor", "tbd"])
        ws["people"].append({"tcSponsor": sp})
    for _ in range(n_spec):
        ws["people"].append({"specSponsor": "spec%d" % rng.randrange(100000)})
    if collective:
        ws["tcSponsorship"] = "collective"
    return ws
```

Then a generic builder:

```python
def _build(n, seed, name_fn, **kw):
    rng = random.Random(seed)
    return [_sig(name_fn(i, rng), rng, **kw) for i in range(n)]
```

Hmm but name_fn may need rng. Fine.

Actually simpler to inline.

Let me write cases with explicit loops.

Case 1:
```python
def _case_many_sigs():
    rng = random.Random(1)
    return [_sig("SIG %d" % i, rng, n_meeting=1, n_slack=1, n_disc=20, n_gc=10, n_tc=10, n_spec=5) for i in range(400)]
```

Hmm, n_disc=20 per sig * 400 = 8000 disc dicts. Fine.

Work per call: 400 * (2 + 20 + 25) = 18800 iterations. person_link called 10000 times (25 per sig... 10 gc + 10 tc + 5 spec = 25 → 10000). Should be a few ms.

Case 2 deep:
```python
[_sig("Deep %d" % i, rng, n_meeting=3, n_slack=2, n_disc=300, n_gc=50, n_tc=50, n_spec=50) for i in range(100)]
```
Work: 100*(5+300+150)=45500. person_link 15000.

Case 3 slack-heavy:
```python
[_sig("Slack %d" % i, rng, n_meeting=1, n_slack=3, n_disc=10, n_gc=5, n_tc=5, n_spec=5) for i in range(250)]
```
Output rows: 250 * (name 10 + schedule 24 + calendar 75 + 3 slack ~200 + details 35) ≈ 250*350 = 87k. OK.

Case 4 people-heavy:
```python
[_sig("People %d" % i, rng, n_meeting=1, n_slack=1, n_disc=5, n_gc=100, n_tc=100, n_spec=100) for i in range(250)]
```
Work: 250*(2+5+300)=76750. person_link 75000. Heavy but maybe too slow? person_link trivial → 75000 calls ~ few ms. Fine.

Hmm, if person_link is expensive (e.g., regex on README content), 75000 calls could be slow. Risky. Let's reduce to 50 each → 37500. Actually, let me keep moderate. Let's do n_gc=40,n_tc=40,n_spec=40 → 30000.

Hmm. Let me keep it reasonable across all cases.

Case 5 collective:
```python
rng = random.Random(5)
sigs = []
for i in range(300):
    sigs.append(_sig("Collective %d" % i, rng, n_meeting=1, n_slack=1, n_disc=10, n_gc=5, n_tc=5, n_spec=5, collective=(i % 2 == 0)))
```

Case 6 meeting-variants: build meetings with/without gdoc/cal. We can control rng to produce variety. Actually _meeting already randomizes. To force variants, write a custom builder. Let me just make a case where all meetings have both gdoc and cal, and another where none. Hmm, but cases are 8. Let me make case 6 = "no-optional-fields": meetings with only schedule.

```python
def _sig_minimal_meeting(...)
```

Simpler: write case 6 with sigs that have meetings lacking gDocNotes/calendarInviteGroup, and no people. That exercises the empty calendar and empty slack paths.

Actually to get empty calendar, the sig must have no calendarInviteGroup. And empty slack → no slack resources. Then row has empty fields.

Case 6: 400 sigs, each 1 meeting with only schedule, no slack, no people, 30 disc. Output rows ~ (10+24+0+0+30)=~70 chars → 400*70=28k. Work: 400*31=12400.

Hmm, that's less work. Add more disc: 100 disc → 400*101=40400. Output still small. Good.

Case 7 special names: names with markdown links and unicode:
```python
def _name7(i, rng):
    base = ["[Spec](https://example.com) SIG", "SIG: C++ / Rust", "Ünïcödé SIG ✨", "SIG #%d" % i, "a"*200]
    ...
```
Hmm, "a"*200 makes long rows → output grows. 300 sigs * 200 chars = 60k just for names. Plus other stuff. Let's keep names moderate.

Let me use varied names: markdown link, unicode, punctuation, mixed case, numbers. Some long-ish (50 chars).

Case 8 mixed-big: 200 sigs, all types, moderate counts.

OK. Also need to make sure names are unique? Not required, but labels distinct. The label is the case label, not name.

Now, output for case 7 with markdown-link names: heading_anchor removes the link but keeps text. Fine.

Let me finalize.

One concern: `_meeting` returns schedule with "%02d" formatting; fine.

Another: In extract_row_data, for meeting, `m.get("gDocNotes")` — if present, notes_link set. Not in output.

Alright, also `calendar` uses `cal` in f-string.

Now, the thunk: `lambda: ("Specification SIGs", sigs)`. But sigs is a module-level list. Since the function doesn't mutate, reuse is fine. But "every call gets the arguments of its own thunk call, all built and kept in memory" — fine.

However, to be safe about mutation, we could return the same list. render_group doesn't mutate. OK.

Let me write it now.

Also: need to make sure that building all inputs takes < 10s. Case 4: 250 sigs * 300 people = 75000 dicts. Fine. Total maybe 300k dicts. Fast.

Let me write final code.

For checks, note the function signature render_group(group_name, sigs).

checks:
1. ("empty-group", lambda: ("Empty", []))
2. ("single-minimal", lambda: ("Minimal", [{"name": "Solo SIG"}]))
3. ("odd-name-none", lambda: ("Odd", [{"name": None, "resources": [], "people": []}]))  -- name None → f-string "None", heading_anchor(None) → re.sub on None raises TypeError. Hmm, that raises. "may raise" ok. But maybe better to have it not raise... Actually heading_anchor(text) with None → text.lower() fails. So raises. Both versions raise. Fine. But maybe I'd rather use a weird string. Let me use ("odd-name", lambda: ("Odd", [{"name": "[Link](x) !! Ünï", "resources": [], "people": []}])). And add a 4th? Only 2-3 allowed. Let's do 3 checks:
- empty
- single minimal
- weird name with special chars

Hmm, "odd type" is suggested. Let me do ("none-sigs", lambda: ("G", None)) as the odd-type check. That raises TypeError. Fine.

Let me pick 3 checks: empty, single-minimal-with-resources, none-sigs.

Actually "single minimal" and "empty" both fine. Let me include the weird-name one instead of none-sigs? The instruction says "empty, one element, None, an odd type". So: empty, one element, odd type (None). Good: 
1. ("empty", lambda: ("Empty Group", []))
2. ("one-element", lambda: ("Solo", [{"name": "Solo SIG", "resources": [], "people": []}]))
3. ("none-sigs", lambda: ("None Group", None))

Good.

Now write the code block.

Let me double check the `_sig` function handles n_meeting=0 (no meeting → meeting_schedule ""). Fine.

Also `ws.get("tcSponsorship")` — only set when collective.

Let me write.

```python
import random


def _meeting(rng):
    m = {"schedule": "Weekly, %s at %02d:00 PT" % (rng.choice(["Mon", "Tue", "Wed", "Thu", "Fri"]), rng.randrange(8, 20))}
    if rng.random() < 0.8:
        m["gDocNotes"] = "1" + "".join(rng.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_") for _ in range(43))
    if rng.random() < 0.7:
        m["calendarInviteGroup"] = "otel-%d" % rng.randrange(1000)
    return {"meeting": m}


def _sig(name, rng, n_meeting=1, n_slack=1, n_disc=0, n_gc=0, n_tc=0, n_spec=0, collective=False):
    ws = {"name": name, "resources": [], "people": []}
    for _ in range(n_meeting):
        ws["resources"].append(_meeting(rng))
    for _ in range(n_slack):
        ws["resources"].append({"slack": {"name": "#chan-%d" % rng.randrange(100000), "id": "C%010d" % rng.randrange(10**10)}})
    for _ in range(n_disc):
        ws["resources"].append({"githubDiscussion": "https://github.com/open-telemetry/community/discussions/%d" % rng.randrange(100000)})
    for _ in range(n_gc):
        ws["people"].append({"gcLiaison": "gc%d" % rng.randrange(1000000)})
    for _ in range(n_tc):
        sp = {"username": "tc%d" % rng.randrange(1000000)}
        if rng.random() < 0.6:
            sp["level"] = rng.choice(["collector", "contributor", "tbd"])
        ws["people"].append({"tcSponsor": sp})
    for _ in range(n_spec):
        ws["people"].append({"specSponsor": "spec%d" % rng.randrange(1000000)})
    if collective:
        ws["tcSponsorship"] = "collective"
    return ws
```

Then build cases at module level (so thunks are cheap).

```python
def _build(n, seed, name_fn, **kw):
    rng = random.Random(seed)
    return [_sig(name_fn(i, rng), rng, **kw) for i in range(n)]
```

Case names.

Let me define name functions.

For case 7, name_fn:
```python
_SPECIAL = [
    "[Specification](https://github.com/open-telemetry/opentelemetry-specification) SIG",
    "SIG: C++ / Rust / Go",
    "Ünïcödé & Spëcial SIG ✨",
    "  Spaced  Name  ",
    "ALL CAPS SIG",
    "sig-with-many-hyphens-and-numbers-1234567890",
    "Mixed CASE Sig 42",
]
def _special_name(i, rng):
    base = _SPECIAL[i % len(_SPECIAL)]
    return "%s %d" % (base, i)
```
Hmm, with 300 sigs, names repeat with index suffix. Fine, diverse enough.

Hmm, adding "%d" makes each name unique-ish. Good.

Now the module-level building:

```python
_CASE1 = _build(400, 11, lambda i, r: "SIG %d" % i, n_meeting=1, n_slack=1, n_disc=20, n_gc=10, n_tc=10, n_spec=5)
```

Wait, n_disc=20 with 400 sigs = 8000 discussion dicts, plus 25 people each = 10000. Fine.

_CASE2 = _build(100, 12, lambda i, r: "Deep SIG %d" % i, n_meeting=3, n_slack=2, n_disc=300, n_gc=50, n_tc=50, n_spec=50)
→ 100*300=30000 disc, 15000 people.

_CASE3 = _build(250, 13, lambda i, r: "Slack SIG %d" % i, n_meeting=1, n_slack=3, n_disc=10, n_gc=5, n_tc=5, n_spec=5)

_CASE4 = _build(250, 14, lambda i, r: "People SIG %d" % i, n_meeting=1, n_slack=1, n_disc=5, n_gc=40, n_tc=40, n_spec=40)
→ 250*120=30000 people.

_CASE5: collective - need per-sig collective flag alternating. Use _build with collective? _build passes kw to all. Let me write manually.

```python
def _build_collective(n, seed):
    rng = random.Random(seed)
    out = []
    for i in range(n):
        out.append(_sig("Collective SIG %d" % i, rng, n_meeting=1, n_slack=1, n_disc=15, n_gc=8, n_tc=8, n_spec=8, collective=(i % 2 == 0)))
    return out
_CASE5 = _build_collective(300, 15)
```

_CASE6: minimal meetings, no slack, no people.
```python
def _build_no_optional(n, seed):
    rng = random.Random(seed)
    out = []
    for i in range(n):
        ws = {"name": "Bare SIG %d" % i, "resources": [], "people": []}
        ws["resources"].append({"meeting": {"schedule": "Biweekly, %s" % rng.choice(["Mon","Wed","Fri"])}})
        for _ in range(100):
            ws["resources"].append({"githubDiscussion": "https://github.com/open-telemetry/community/discussions/%d" % rng.randrange(100000)})
        out.append(ws)
    return out
_CASE6 = _build_no_optional(400, 16)
```
Output rows: name ~11 + schedule ~15 + empty + empty + details ~35 = ~65 chars → 400*65=26k. Work 400*101=40400.

_CASE7 = _build(300, 17, _special_name, n_meeting=1, n_slack=1, n_disc=10, n_gc=5, n_tc=5, n_spec=5)

_CASE8 = _build(200, 18, lambda i, r: "Mixed SIG %d" % i, n_meeting=2, n_slack=1, n_disc=150, n_gc=30, n_tc=30, n_spec=30)

Good.

Now the thunks return (group_name, sigs).

Let me double check output sizes:
- Case1: 400 rows * ~218 = 87k. OK.
- Case2: 100 rows, 2 slack → ~280 chars → 28k.
- Case3: 250 rows, 3 slack → ~350 → 87k. OK.
- Case4: 250 rows, 1 slack → ~200 → 50k.
- Case5: 300 rows → ~65k.
- Case6: 26k.
- Case7: 300 rows with varying names → maybe 60-80k.
- Case8: 200 rows → ~45k.

All under ~100k. 

Hmm case3 87k is close but "about 100 000". OK.

Actually let me reduce case3 to 220 sigs → 77k. Meh, fine. Keep 250? Let me use 220 for safety.

Hmm, actually let me reconsider: the row for case3: name "Slack SIG 123" (13), " | " separators, schedule "Weekly, Tue at 08:00 PT" (23), calendar link "[otel-123](https://groups.google.com/a/opentelemetry.io/g/otel-123)" (69), 3 slack links each "[#chan-12345](https://cloud-native.slack.com/archives/C0123456789)" (63) joined with ", " → 63*3+4=193, details "[Details](./sigs.md#slack-sig-123)" (33). Total ≈ 13+23+69+193+33 + 6 separators*3 + 4 = ~350. 250*350 = 87.5k. Plus header. Slightly over 87k. Let's use 200 sigs → 70k.

I'll set case3 to 200.

Also case1: 400 * 218 = 87k. Reduce to 350 → 76k. Eh. Let's keep 400; 87k is "about 100k". Hmm, the limit says "under about 100 000". 87k is under. Fine.

Actually, to be safer, let me reduce case1 to 350. And case7 to 250.

Let me finalize numbers:
- Case1: 350 sigs
- Case2: 100
- Case3: 200
- Case4: 250
- Case5: 300
- Case6: 400
- Case7: 250
- Case8: 200

Now, timing: is one call ~1ms? Case1: 350*(2+20+25)=16450 iterations with string formatting. Probably ~3-5 ms. Good. Case2: 100*455=45500 → ~10ms. Case4: 250*(2+5+120)=31750 → ~7ms. Good.

Total across cases per "run" maybe 50ms. Fine.

Let me now also double-check: does the function need `sigs` to be a list (iterable)? Yes.

One more: `extract_row_data` accesses `ws["name"]` in roadmap branch only; not used.

Also `repository_link` not called since no repository resources. Good.

Now, potential issue: `person_link` might do something that fails for our usernames. E.g., if it looks up a mapping and returns None → fallback. Fine.

Let me write final.

Also need `checks()` labels distinct and `cases()` labels distinct.

Write the code.

Actually, one more consideration about module import: `importlib.import_module('update-sig-tables')`. The harness handles sys.path presumably. We just write the functions.

Final code:

```python
import random


def _meeting(rng):
    m = {"schedule": "Weekly, %s at %02d:00 PT" % (rng.choice(["Mon", "Tue", "Wed", "Thu", "Fri"]), rng.randrange(8, 20))}
    if rng.random() < 0.8:
        m["gDocNotes"] = "1" + "".join(rng.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_") for _ in range(43))
    if rng.random() < 0.7:
        m["calendarInviteGroup"] = "otel-%d" % rng.randrange(1000)
    return {"meeting": m}


def _sig(name, rng, n_meeting=1, n_slack=1, n_disc=0, n_gc=0, n_tc=0, n_spec=0, collective=False):
    ...
```

OK writing it all.

Let me make sure `_build` is defined before use at module level.

I'll write it now in the final answer.

Double-check the `_sig` for n_meeting=0: resources may be empty → extract_row_data returns defaults. Fine.

Let me produce the final block.