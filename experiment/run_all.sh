#!/usr/bin/env bash
# Runs the experiment grid, one run at a time. Run it again to resume: finished
# runs are skipped.
#
#   ./run_all.sh --check                          one tiny API call (< $0.01)
#   ./run_all.sh --dry-run --repos gedcom         the whole pipeline without Claude (free)
#   tmux new-session -d -s exp "$(pwd)/experiment/run_all.sh --repos amazon-neptune-tools"
#
# Options: --repos "a b"   --arms "full control"   --models "claude-haiku-5-5"
#          --again   re-run finished runs; the previous one is kept as <model>.1, .2, ...
#          --effort medium   one level for every model, instead of config.sh's EFFORT / EFFORT_OF
#
# One run = one repo x one arm x one model:
#   1. $RUN gets a fresh copy of the repo (with the arm's skill in .claude/skills),
#      a fresh copy of the repo's venv, and an empty Claude config holding a
#      one-time copy of the API key.
#   2. The input service starts (tools/inputs/service.py): it generates the
#      inputs the agent's repairs are measured on, when the agent asks.
#   3. $EXP is locked, so the agent cannot read our keys, clones or results.
#   4. claude -p runs in the repo; any command is allowed.
#   5. $EXP is unlocked; the input service finishes what was asked; the agent's
#      outputs are saved, whatever it created in /tmp is listed and deleted, its
#      submissions are re-measured by tools/review.py on our copy of the inputs,
#      and a row goes into archive/summary.csv.

set -uo pipefail
source "$(dirname "$0")/config.sh"

REPOS=()
DRY=0
CHECK=0
AGAIN=0
while [ $# -gt 0 ]; do
  case "$1" in
    --repos)   read -r -a REPOS <<< "$2"; shift 2 ;;
    --arms)    read -r -a ARMS <<< "$2"; shift 2 ;;
    --models)  read -r -a MODELS <<< "$2"; shift 2 ;;
    --auth)    AUTH="$2"; shift 2 ;;      # api | subscription, this invocation only
    --effort)  EFFORT="$2"; EFFORT_OF=(); shift 2 ;;   # every model, this invocation only
    --dry-run) DRY=1; shift ;;
    --check)   CHECK=1; shift ;;
    --again)   AGAIN=1; shift ;;
    *) echo "unknown option: $1"; exit 2 ;;
  esac
done
[ ${#REPOS[@]} -eq 0 ] && mapfile -t REPOS < <(cut -f1 "$HARNESS/repos.tsv")
case "$AUTH" in
  api) ;;
  subscription) [ -s "$EXP/oauth-token" ] || { echo "AUTH=subscription needs $EXP/oauth-token: run \`claude setup-token\` and save the token there"; exit 2; } ;;
  *) echo "unknown AUTH: $AUTH (api or subscription)"; exit 2 ;;
esac

CLAUDE=$(command -v claude)
mkdir -p "$EXP/archive" "$EXP/logs"

log() { echo "[$(date '+%F %T')] $*" | tee -a "$EXP/logs/driver.log"; }

lock()   { chmod 000 "$EXP"; }
unlock() { chmod 700 "$EXP"; }
INPUTS_PID=
trap 'unlock; [ -n "$INPUTS_PID" ] && kill "$INPUTS_PID" 2>/dev/null' EXIT
trap 'unlock; exit 130' INT TERM

# The API key is never in the environment. Claude fetches it once, through a
# helper that deletes the one-time copy as it reads it -- before the agent can
# run a single command -- and keeps it in memory for the rest of the session.
key_once() {
  OAUTH=
  if [ "$AUTH" = subscription ]; then
    # A claude.ai plan instead: the one-year token `claude setup-token` prints,
    # kept in $EXP/oauth-token and read now, before the lock. Claude needs it in
    # its environment, so every shell Claude starts sources unset.sh
    # (CLAUDE_ENV_FILE, claude_run) and the agent's commands run without it.
    # CLAUDE_CODE_SUBPROCESS_ENV_SCRUB would do the same, but needs bubblewrap.
    # No apiKeyHelper: it would outrank the token.
    OAUTH=$(cat "$EXP/oauth-token")
    echo '{}' > "$RUN/claude-config/settings.json"
    echo 'unset CLAUDE_CODE_OAUTH_TOKEN' > "$RUN/claude-config/unset.sh"
    chmod 444 "$RUN/claude-config/unset.sh"
    return
  fi
  cp "$EXP/api-key" "$RUN/claude-config/.key"
  printf '{"apiKeyHelper": "cat %s/.key && rm -f %s/.key"}\n' \
    "$RUN/claude-config" "$RUN/claude-config" > "$RUN/claude-config/settings.json"
}

# Claude in the current directory, with a clean environment, and no dollar cap:
# --max-budget-usd is shown to the model every turn (config.sh says why).
claude_run() {  # model, prompt
  local auth=()
  [ -n "$OAUTH" ] && auth=("CLAUDE_CODE_OAUTH_TOKEN=$OAUTH" CLAUDE_ENV_FILE="$RUN/claude-config/unset.sh")
  env -i "${auth[@]}" HOME="$HOME" USER="$USER" LOGNAME="$USER" SHELL=/bin/bash \
    LANG="${LANG:-C.UTF-8}" TERM=xterm-256color \
    PATH="$RUN/venv/bin:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin" VIRTUAL_ENV="$RUN/venv" \
    TMPDIR="$RUN/tmp" ENERGY_INPUTS_SOCKET="$RUN/inputs.sock" \
    CLAUDE_CONFIG_DIR="$RUN/claude-config" CLAUDE_CODE_API_KEY_HELPER_TTL_MS=86400000 \
    timeout -k 2m -s INT "$AGENT_TIMEOUT" \
    "$CLAUDE" -p "$2" --model "$1" --effort "${EFFORT_OF[$1]:-$EFFORT}" \
      --permission-mode bypassPermissions --permission-prompts none \
      --output-format stream-json --verbose < /dev/null
}

if [ "$CHECK" = 1 ]; then
  rm -rf "$RUN"; mkdir -p "$RUN/check" "$RUN/claude-config"; cd "$RUN/check" || exit 1
  key_once
  # API: the key copy is gone before the agent's first command (expect 0).
  # Subscription: no credential is visible to the agent's commands (expect 0).
  if [ "$AUTH" = subscription ]; then
    probe="env | grep -c -e sk-ant- -e '^ANTHROPIC_' -e '^CLAUDE_CODE_OAUTH_TOKEN='; env | grep -c ENERGY_INPUTS_SOCKET"
  else
    probe="ls $RUN/claude-config/.key 2>/dev/null | wc -l"
  fi
  claude_run claude-haiku-5-5 \
    "Run this shell command and reply with only its output: $probe" \
    > out.jsonl 2> err.log
  echo "exit=$?"; head -3 err.log
  python3 - out.jsonl <<'EOF'
import json, sys
for line in open(sys.argv[1]):
    d = json.loads(line)
    if d.get("type") == "system" and d.get("subtype") == "init":
        print("credential:", d.get("apiKeySource"))
    if d.get("type") == "result":
        print("result:", d.get("subtype"), "| reply:", repr(str(d.get("result")).strip()),
              "(first 0 = the agent could not see a credential; with a subscription, second 1 = our socket is still there) | cost $",
              d.get("total_cost_usd"), "(list-price estimate)")
EOF
  cd /; rm -rf "$RUN"; exit 0
fi

fake_agent() {  # dry run: write what an agent writes, and test the lock
  echo '{"type":"system","subtype":"init","model":"dry-run"}'
  printf '{"type":"assistant","message":{"content":[{"type":"tool_use","name":"Bash","input":{"command":"ls %s"}}]}}\n' "$EXP"
  printf '{"type":"user","message":{"content":[{"type":"tool_result","content":"%s"}]}}\n' \
    "$(ls "$EXP" 2>&1 | head -1)"
  # DRY_UNIT=path::qualname also asks the input service for that unit's inputs.
  if [ -n "${DRY_UNIT:-}" ]; then
    "$RUN/venv/bin/python" .claude/skills/*/scripts/inputs.py request "$DRY_UNIT" >&2
  fi
  echo '{"type":"result","subtype":"success","total_cost_usd":0,"num_turns":1,"modelUsage":{}}'
  echo '{"step": 1, "dry_run": true}' > step1.jsonl
}

# What the agent left in /tmp, listed in the run folder and deleted, so the next
# run cannot read this one's repairs. Only entries that did not exist when the
# agent started and that belong to us; Claude Code's own folders stay. Run again
# around our review, into its own list: a repository's module-level code can
# write to an absolute /tmp path while verify.py loads it (Oct 22:
# colbert-long/scripts/convert.py opened /tmp/vespa_feed_file_en.json).
clean_tmp() {  # run folder, list file
  local out=$1 list=${2:-tmp_created.txt}
  ls -A /tmp | sort | comm -13 "$out/.tmp_before" - \
    | grep -v -E '^(claude-|cc-daemon-|tmux-|systemd-private-)' \
    | while read -r name; do
        [ -O "/tmp/$name" ] || continue
        echo "/tmp/$name"
        rm -rf -- "/tmp/$name"
      done > "$out/$list"
  rm -f "$out/.tmp_before"
}

# The input service (tools/inputs/service.py) generates the inputs the agent's
# repairs are measured on, outside its session. Started before the lock: it
# reads the OpenRouter key, copies the pristine clone and opens the cache and
# our copy of the inputs while it still can. Finished after the agent, so every
# unit the agent asked for is done before the review measures with our copy.
start_inputs() {  # repo, run folder, root-cause cards folder (empty when the arm has none), scanner (1 when the arm has rules)
  local repo=$1 out=$2 cards=$3 scanner=$4 waited=0
  rm -f "$RUN/inputs.sock"
  # It also keeps each step's files when the agent says the step is finished,
  # every repair verify.py measures, and opens the root-cause cards at step 2;
  # with rules, `done 1` waits until scan.py compared them with step1.jsonl
  # (tools/inputs/steps.py), all in $out/record.
  "$RUN/venv/bin/python" "$PROJECT/tools/inputs/service.py" --repo-name "$repo" \
    --pristine "$EXP/pristine/$repo" --repo "$RUN/$repo" --socket "$RUN/inputs.sock" \
    --cache "$EXP/inputs-cache" --out "$out/inputs" --key "$EXP/openrouter-key" \
    --work "$RUN/inputs-work" --record "$out/record" ${cards:+--cards "$cards"} ${scanner:+--scanner} \
    > "$out/inputs-service.log" 2>&1 &
  INPUTS_PID=$!
  until [ -S "$RUN/inputs.sock" ]; do
    if ! kill -0 "$INPUTS_PID" 2>/dev/null || [ $waited -ge 300 ]; then
      log "input service did not start: $(tail -2 "$out/inputs-service.log" | tr '\n' ' ')"
      kill "$INPUTS_PID" 2>/dev/null
      return 1
    fi
    sleep 1; waited=$((waited + 1))
  done
}

finish_inputs() {  # run folder
  local out=$1
  ENERGY_INPUTS_SOCKET="$RUN/inputs.sock" "$RUN/venv/bin/python" - "$PROJECT/src" \
    >> "$out/inputs-service.log" 2>&1 <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
from lib.inputs import ask
print("finish:", ask({"op": "finish", "wait_s": 900}, timeout=960))
PY
  sleep 2
  kill "$INPUTS_PID" 2>/dev/null
  wait "$INPUTS_PID" 2>/dev/null
}

save_outputs() {  # repo dir, run folder
  local w=$1 out=$2
  mkdir -p "$out/agent"
  for f in step1.jsonl step2.jsonl step3.jsonl submissions.jsonl; do
    if [ -f "$w/$f" ]; then
      cp "$w/$f" "$out/agent/"
      continue
    fi
    # Written somewhere else in the repository (one run put both in
    # .energy-scan/): still reviewed, and the place recorded.
    local found
    found=$(find "$w" -name "$f" -not -path "*/.git/*" -not -path "$w/.claude/*" \
              -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)
    if [ -n "$found" ]; then
      cp "$found" "$out/agent/$f"
      echo "${found#"$w"/}" >> "$out/outputs_misplaced.txt"
    fi
  done
  # The three steps' output, in order, as one findings.jsonl: what the review
  # and the summary read. A finished step is our copy from `done`
  # ($out/record/steps); an unfinished one is the file as the session left it.
  for n in 1 2 3; do
    for f in "$out/record/steps/step$n.jsonl" "$out/record/steps/unfinished/step$n.jsonl" \
             "$out/agent/step$n.jsonl"; do
      [ -f "$f" ] && { cat "$f"; break; }
    done
  done > "$out/agent/findings.jsonl"
  chmod -R u+w "$out/agent" 2>/dev/null
  [ -d "$w/.energy-scan" ] && cp -r "$w/.energy-scan" "$out/agent/"
  # The agent's view of its inputs, to compare with our copy in $out/inputs.
  # The service leaves them read-only; the copy is made writable so it can go.
  if [ -d "$w/.energy-inputs" ]; then
    cp -r "$w/.energy-inputs" "$out/agent/"
    chmod -R u+w "$out/agent/.energy-inputs" "$w/.energy-inputs"
  fi
  # Anything else it changed in the repository, which it was told not to do.
  git -C "$w" status --porcelain --untracked-files=all \
    | grep -v -E ' \.claude/|step[1-4]\.jsonl$|submissions\.jsonl$|\.energy-scan/|\.energy-inputs/|__pycache__|\.pyc$' \
    > "$out/repo_changes.txt"
  git -C "$w" diff > "$out/repo_changes.diff"
}

# Stop the grid, rather than start a run the disk cannot finish. Run again
# once space is freed: finished runs are skipped.
enough_space() {
  local home_gb tmp_gb
  home_gb=$(df -BG --output=avail "$HOME" | tail -1 | tr -dc 0-9)
  tmp_gb=$(df -BG --output=avail /tmp | tail -1 | tr -dc 0-9)
  if [ "$home_gb" -lt "$MIN_FREE_GB" ] || [ "$tmp_gb" -lt "$MIN_TMP_GB" ]; then
    log "STOP: ${home_gb} GB free on $HOME (need $MIN_FREE_GB), ${tmp_gb} GB on /tmp (need $MIN_TMP_GB)"
    return 1
  fi
}

# "limit <message>" or "error <message>" when the agent's session ended on an API
# error before `step.py done 3`; nothing otherwise. A session that finished step
# 3 is a run even if a later turn hit the limit (Opus, Oct 21: 50 turns, then
# one more woken by a background command). The same for --auth api and
# subscription: an API key over its limit or out of credit is a limit too.
cut_reason() {  # run folder
  python3 - "$1" <<'EOF'
import json, re, sys
from pathlib import Path
out = Path(sys.argv[1])
results = []
for line in open(out / "transcript.jsonl", errors="replace"):
    try:
        event = json.loads(line)
    except ValueError:
        continue
    if isinstance(event, dict) and event.get("type") == "result":
        results.append(event)
finished = False
try:
    for line in open(out / "record" / "events.jsonl"):
        row = json.loads(line)
        finished = finished or (row.get("event") == "done" and row.get("step") == 3)
except (OSError, ValueError):
    pass
last = results[-1] if results else {}
if last.get("is_error") and (last.get("terminal_reason") == "api_error" or last.get("api_error_status")) and not finished:
    message = " ".join(str(last.get("result") or "API error").split())[:300]
    limit = last.get("api_error_status") == 429 or re.search(r"limit|credit balance|quota|billing", message, re.I)
    print(("limit " if limit else "error ") + message)
EOF
}

run_one() {  # repo, arm, model
  local repo=$1 arm=$2 model=$3
  local name=${model#claude-}; name=${name%%-*}
  local id=$repo.$arm.$name
  # A dry run never touches the real archive or its summary.csv.
  local archive=$EXP/archive
  [ "$DRY" = 1 ] && archive=$EXP/archive-dry
  local out=$archive/$repo/$arm/$name
  if [ -f "$out/meta.json" ]; then
    [ "$AGAIN" = 1 ] || { log "skip $id (done)"; return; }
    local n=1
    while [ -e "$out.$n" ]; do n=$((n + 1)); done
    mv "$out" "$out.$n"
    log "kept the previous $id as $out.$n"
  fi

  [ -d "$RUN" ] && chmod -R u+w "$RUN" 2>/dev/null
  rm -rf "$RUN" "$out"
  mkdir -p "$RUN/claude-config" "$out"
  cp -a "$EXP/pristine/$repo" "$RUN/$repo"
  mkdir -p "$RUN/$repo/.claude/skills"
  cp -r "$PROJECT/${SKILL[$arm]}" "$RUN/$repo/.claude/skills/"
  tar -xf "$EXP/venvs/$repo.tar" -C "$RUN"
  mkdir -p "$RUN/tmp" "$RUN/tmp-review"
  key_once
  # What the agent installs into its venv stays for the review, which measures
  # in the same venv; before and after, for the audit.
  "$RUN/venv/bin/python" -m pip freeze > "$out/venv_before.txt" 2>/dev/null
  ls -A /tmp | sort > "$out/.tmp_before"
  local cards="$RUN/$repo/.claude/skills/${SKILL[$arm]##*/}/reference/root-causes"
  [ -d "$cards" ] || cards=
  local scanner=
  [ -f "$RUN/$repo/.claude/skills/${SKILL[$arm]##*/}/scripts/scan.py" ] && scanner=1
  if ! start_inputs "$repo" "$out" "$cards" "$scanner"; then
    log "skip $id: no input service"
    rm -rf "$RUN"
    return
  fi

  log "start $id"
  local start=$SECONDS rc started
  started=$(date -Is)
  exec 3> "$out/transcript.jsonl" 4> "$out/stderr.log"  # opened before the lock
  lock
  if [ "$DRY" = 1 ]; then
    (cd "$RUN/$repo" && ENERGY_INPUTS_SOCKET="$RUN/inputs.sock" fake_agent) >&3 2>&4
  else
    (cd "$RUN/$repo" && claude_run "$model" "${PROMPT[$arm]}") >&3 2>&4
  fi
  rc=$?
  # Our folder's mode as the agent left it, before we open it again: anything
  # but 000 means the agent (same user) unlocked it. summarize.py flags it.
  local exp_mode
  exp_mode=$(stat -c %a "$EXP")
  unlock
  [ "$exp_mode" = 0 ] || log "WARNING $id: $EXP was mode $exp_mode when the agent ended, not 000"
  exec 3>&- 4>&-
  local agent_s=$((SECONDS - start))
  log "agent done $id: exit $rc after $((agent_s / 60)) min"
  finish_inputs "$out"
  [ -n "$cards" ] && chmod u+rwx "$cards" 2>/dev/null   # the service opens them; in case it died

  save_outputs "$RUN/$repo" "$out"
  # A session the API ended before step 3 was finished is not a run: it is set
  # aside, not reviewed or archived as done, so the next invocation runs it
  # again. On a usage limit -- the plan's, or the API key's -- nothing else
  # starts either: the next run would end the same way, and be archived too.
  local cut
  cut=$(cut_reason "$out")
  if [ -n "$cut" ]; then
    clean_tmp "$out"
    local aside
    aside="$out.cut-$(date +%Y%m%d-%H%M%S)"
    mv "$out" "$aside"
    chmod -R u+w "$RUN" 2>/dev/null
    rm -rf "$RUN"
    if [ "${cut%% *}" = limit ]; then
      log "STOPPED at $id: the session hit a usage limit before step 3 was finished: ${cut#* }"
      log "  not counted (kept in $aside), and nothing else starts. Run the same command again once the limit resets: finished runs are skipped, this one is redone."
      exit 3
    fi
    log "SET ASIDE $id: the session ended on an API error before step 3 was finished: ${cut#* } (kept in $aside); it runs again next time"
    return
  fi
  # Every rule, on the untouched repository, in every arm: which of the agent's
  # findings a rule also flags is measured here (summarize.py), not asked of the
  # agent. The full arm's scanner has every rule.
  (cd "$out" && "$RUN/venv/bin/python" "$PROJECT/dist/full/energy-smells/scripts/scan.py" \
     "$EXP/pristine/$repo" --json --out "$out/rules-detail" > "$out/rules.json" 2> "$out/rules.log") \
    || log "rule scan failed for $id: $(tail -1 "$out/rules.log")"
  "$RUN/venv/bin/python" -m pip freeze > "$out/venv_after.txt" 2>/dev/null
  clean_tmp "$out"

  local status=no_submissions review_start=$SECONDS
  if [ "$DRY" = 1 ]; then
    status=dry_run
  elif [ -s "$out/record/submissions_all.jsonl" ] || [ -s "$out/agent/submissions.jsonl" ]; then
    log "review $id"
    ls -A /tmp | sort > "$out/.tmp_before"
    mkdir -p "$out/review"
    # Every repair the agent ever wrote: its final file, plus any line it
    # removed during the session, as last seen (record/submissions_all.jsonl).
    if [ -s "$out/record/submissions_all.jsonl" ]; then
      cp "$out/record/submissions_all.jsonl" "$out/review/submissions.jsonl"
    else
      cp "$out/agent/submissions.jsonl" "$out/review/"
    fi
    cp "$out/agent/findings.jsonl" "$out/review/" 2>/dev/null || : > "$out/review/findings.jsonl"
    if TMPDIR="$RUN/tmp-review" timeout -k 1m "$REVIEW_TIMEOUT" "$RUN/venv/bin/python" "$PROJECT/tools/review.py" \
         "$EXP/pristine/$repo" "$out/review" --inputs "$out/inputs" > "$out/review.log" 2>&1; then
      status=done
    else
      status=review_failed
    fi
    clean_tmp "$out" tmp_created_review.txt
  fi

  printf '{"run_id":"%s","repo":"%s","repo_commit":"%s","arm":"%s","model":"%s","effort":"%s",' \
    "$id" "$repo" "$(awk -v r="$repo" '$1 == r {print $3}' "$HARNESS/repos.tsv")" "$arm" "$model" "${EFFORT_OF[$model]:-$EFFORT}" > "$out/run.json"
  printf '"auth":"%s",' "$AUTH" >> "$out/run.json"
  printf '"status":"%s","agent_exit":%d,"agent_seconds":%d,"review_seconds":%d,"started":"%s","exp_mode_at_end":"%s",' \
    "$status" "$rc" "$agent_s" "$((SECONDS - review_start))" "$started" "$exp_mode" >> "$out/run.json"
  printf '"project_commit":"%s","project_uncommitted_files":%d,"claude_version":"%s","exp":"%s","run":"%s","project":"%s"}\n' \
    "$(git -C "$PROJECT" rev-parse HEAD)" "$(git -C "$PROJECT" status --porcelain -- src build dist tools | wc -l)" \
    "$("$CLAUDE" --version)" "$EXP" "$RUN" "$PROJECT" >> "$out/run.json"

  python3 "$HARNESS/lib/summarize.py" "$out" > /dev/null
  log "finished $id: $status"
  chmod -R u+w "$RUN" 2>/dev/null
  rm -rf "$RUN"
}

log "grid: ${#REPOS[@]} repo(s) x ${#ARMS[@]} arm(s) x ${#MODELS[@]} model(s)$([ "$DRY" = 1 ] && echo ' [dry run]')"
for repo in "${REPOS[@]}"; do
  [ -f "$EXP/venvs/$repo.tar" ] || { log "no venv for $repo: run ./setup_venvs.sh $repo"; continue; }
  for model in "${MODELS[@]}"; do
    for arm in "${ARMS[@]}"; do
      enough_space || exit 1
      run_one "$repo" "$arm" "$model"
    done
  done
done
log "all done: $EXP/archive/summary.csv"
