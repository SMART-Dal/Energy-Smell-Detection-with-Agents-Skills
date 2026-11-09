#!/usr/bin/env bash
# Use a skill on your own repository: install it, start the input service, and
# open Claude Code in the repository.
#
#   ./use_skill.sh REPO [--skill full|core+tax|core] [--python PATH | --new-venv]
#                       [--key FILE] [--review] [-- CLAUDE OPTIONS]
#
#   REPO          the repository to analyse
#   --skill       which skill to install (default: full)
#   --python      the Python of the venv the repository's code runs in
#                 (default: $VIRTUAL_ENV, then REPO/.venv, then REPO/venv)
#   --new-venv    create REPO/.venv and install the repository's dependencies into it
#   --key         file holding your OpenRouter key (default: ~/.energy-skill/openrouter-key)
#   --review      after the session, measure every submitted repair again and write a report
#   -- ...        passed to `claude`, for example: -- --model sonnet
#
# The skill's packages (requirements-skill.txt) are installed into the venv if
# they are missing. In the session, ask for example:
#
#   Find the energy smells in this repository using the energy-smells skill.
#   Find the energy smells in src/parser.py using the energy-smells skill.
#
# (For the core skill: "Find where this repository wastes energy, using the
# energy-efficiency skill.") Session files are kept in ~/.energy-skill/sessions/.
set -uo pipefail
TOOL=$(cd "$(dirname "$0")" && pwd)

repo= skill=full python= new_venv=0 review=0 key=$HOME/.energy-skill/openrouter-key
claude_args=()
while [ $# -gt 0 ]; do
  case "$1" in
    --skill)    skill=$2; shift 2 ;;
    --python)   python=$2; shift 2 ;;
    --new-venv) new_venv=1; shift ;;
    --key)      key=$2; shift 2 ;;
    --review)   review=1; shift ;;
    --)         shift; claude_args=("$@"); break ;;
    -h|--help)  sed -n '2,24p' "$0"; exit 0 ;;
    -*)         echo "unknown option: $1"; exit 2 ;;
    *)          repo=$1; shift ;;
  esac
done
[ -n "$repo" ] && [ -d "$repo" ] || { echo "usage: ./use_skill.sh REPO [options]  (see --help)"; exit 2; }
repo=$(cd "$repo" && pwd)

case "$skill" in
  full)     src=$TOOL/dist/full/energy-smells ;;
  core+tax) src=$TOOL/dist/core+tax/energy-smells ;;
  core)     src=$TOOL/dist/core/energy-efficiency ;;
  *) echo "unknown skill: $skill (full, core+tax or core)"; exit 2 ;;
esac
name=$(basename "$src")
[ -s "$key" ] || { echo "no OpenRouter key in $key: save your key there (one line, chmod 600), or pass --key FILE"; exit 2; }

# The venv the repository's code runs in.
if [ "$new_venv" = 1 ]; then
  python=$repo/.venv/bin/python
  if [ ! -x "$python" ]; then
    echo "Creating $repo/.venv"
    "${PYTHON:-python3}" -m venv "$repo/.venv" || exit 1
    "$python" -m pip install -q --upgrade pip
  fi
  echo "Installing the repository's dependencies and the skill's packages (one pip resolve)"
  "$python" "$TOOL/experiment/lib/repo_deps.py" "$repo" -r "$TOOL/requirements-skill.txt" || exit 1
fi
if [ -z "$python" ]; then
  for candidate in "${VIRTUAL_ENV:-}/bin/python" "$repo/.venv/bin/python" "$repo/venv/bin/python"; do
    [ -x "$candidate" ] && { python=$candidate; break; }
  done
fi
[ -n "$python" ] && [ -x "$python" ] || {
  echo "no venv found: activate the repository's venv, pass --python PATH, or use --new-venv"; exit 2; }
venv=$(cd "$(dirname "$python")/.." && pwd)
"$python" -c 'import sys; assert sys.version_info >= (3, 10)' 2>/dev/null \
  || { echo "$python is older than Python 3.10"; exit 2; }
if ! "$python" -c 'import codegreen' 2>/dev/null || { [ "$skill" = full ] && [ ! -x "$venv/bin/ruff" ]; }; then
  echo "Installing requirements-skill.txt into $venv"
  "$python" -m pip install -q -r "$TOOL/requirements-skill.txt" || exit 1
fi
ls /sys/class/powercap/intel-rapl:*/energy_uj > /dev/null 2>&1 \
  || echo "WARNING: no RAPL counters on this machine; energy cannot be measured"

# Install exactly one energy skill into the repository.
mkdir -p "$repo/.claude/skills"
rm -rf "$repo/.claude/skills/energy-smells" "$repo/.claude/skills/energy-efficiency"
cp -r "$src" "$repo/.claude/skills/$name"
echo "Installed the $skill skill in $repo/.claude/skills/$name"

# The input service writes the inputs repairs are measured on, outside the session.
session=$HOME/.energy-skill/sessions/$(basename "$repo")-$(date +%Y%m%d-%H%M%S)
mkdir -p "$session"
cards=$repo/.claude/skills/$name/reference/root-causes
[ -d "$cards" ] || cards=
scanner=
[ -f "$repo/.claude/skills/$name/scripts/scan.py" ] && scanner=1
"$python" "$TOOL/tools/inputs/service.py" --repo-name "$(basename "$repo")" \
  --pristine "$repo" --repo "$repo" --socket "$session/inputs.sock" \
  --cache "$HOME/.energy-skill/inputs-cache" --out "$session/inputs" --key "$key" \
  --work "$session/work" --record "$session/record" ${cards:+--cards "$cards"} ${scanner:+--scanner} \
  > "$session/inputs-service.log" 2>&1 &
service=$!
for _ in $(seq 300); do
  [ -S "$session/inputs.sock" ] && break
  kill -0 "$service" 2>/dev/null || { echo "the input service did not start:"; tail -5 "$session/inputs-service.log"; exit 1; }
  sleep 1
done
[ -n "$cards" ] && trap 'chmod -R u+rwX "$cards" 2>/dev/null' EXIT

echo "Starting Claude Code in $repo"
(cd "$repo" && ENERGY_INPUTS_SOCKET="$session/inputs.sock" VIRTUAL_ENV="$venv" \
   PATH="$venv/bin:$PATH" claude "${claude_args[@]}")

echo "Session over; waiting for any inputs still being generated"
ENERGY_INPUTS_SOCKET="$session/inputs.sock" "$python" - "$TOOL/src" >> "$session/inputs-service.log" 2>&1 <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
from lib.inputs import ask
print("finish:", ask({"op": "finish", "wait_s": 900}, timeout=960))
PY
kill "$service" 2>/dev/null
wait "$service" 2>/dev/null

# The agent's files, for the review.
mkdir -p "$session/review"
for n in 1 2 3; do
  for f in "$session/record/steps/step$n.jsonl" "$session/record/steps/unfinished/step$n.jsonl" "$repo/step$n.jsonl"; do
    [ -f "$f" ] && { cat "$f"; break; }
  done
done > "$session/review/findings.jsonl"
if [ -s "$session/record/submissions_all.jsonl" ]; then
  cp "$session/record/submissions_all.jsonl" "$session/review/submissions.jsonl"
elif [ -s "$repo/submissions.jsonl" ]; then
  cp "$repo/submissions.jsonl" "$session/review/submissions.jsonl"
fi
echo "Session files: $session"
if [ -s "$session/review/submissions.jsonl" ]; then
  command=("$python" "$TOOL/tools/review.py" "$repo" "$session/review" --inputs "$session/inputs")
  if [ "$review" = 1 ]; then
    echo "Measuring every repair again (about a minute each)"
    "${command[@]}" && echo "Report: $session/review/REPORT.md"
  else
    echo "To measure every repair again and write a report:"
    printf '  %q' "${command[@]}"; echo
  fi
fi
