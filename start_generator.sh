#!/usr/bin/env bash
# Start the input generator for your project, and leave it running while you use
# the skill in Claude Code. It stops when you press Ctrl-C or close its terminal.
#
#   dr-greens/start_generator.sh PROJECT KEY_FILE
#
# Run it with your project's venv activated. It records where it listens in
# PROJECT/.claude/settings.local.json, so Claude Code sessions in the project find
# it. Its own files are kept in ~/.energy-skill/<project>; set ENERGY_SKILL_HOME
# to use another folder.
set -euo pipefail

tool=$(cd "$(dirname "$0")" && pwd)
[ -f "$tool/tools/inputs/service.py" ] || { echo "Run start_generator.sh from the unzipped dr-greens folder; do not copy it."; exit 1; }
repo=$(cd "$1" && pwd)
key=$(cd "$(dirname "$2")" && pwd)/$(basename "$2")
name=$(basename "$repo")
skill=$(ls -d "$repo"/.claude/skills/energy-* 2>/dev/null | head -1 || true)
[ -n "$skill" ] || { echo "No skill in $repo/.claude/skills: copy one there first."; exit 1; }
[ -s "$key" ] || { echo "No key in $key: save your OpenRouter key there."; exit 1; }

home=${ENERGY_SKILL_HOME:-$HOME/.energy-skill}/$name
session=$home/sessions/$(date +%Y%m%d-%H%M%S)
socket=${XDG_RUNTIME_DIR:-/tmp}/energy-inputs-$name.sock    # a socket path is limited to 108 characters
mkdir -p "$session"

# Replace a generator already running for this project, and start clean.
pid=$(cat "$home/generator.pid" 2>/dev/null || true)
if [ -n "$pid" ] && grep -qs service.py "/proc/$pid/cmdline"; then kill "$pid"; sleep 1; fi
rm -f "$socket"
cards=$skill/reference/root-causes
[ -d "$cards" ] && chmod -R u+rwX "$cards"

# Tell Claude Code sessions in the project where the generator listens.
python - "$repo/.claude/settings.local.json" "$socket" <<'PY'
import json, os, sys
path, socket = sys.argv[1], sys.argv[2]
settings = json.load(open(path)) if os.path.exists(path) else {}
settings.setdefault("env", {})["ENERGY_INPUTS_SOCKET"] = socket
json.dump(settings, open(path, "w"), indent=2)
PY

args=(--repo-name "$name" --pristine "$repo" --repo "$repo" --key "$key"
      --socket "$socket" --cache "$home/cache"
      --out "$session/inputs" --work "$session/work" --record "$session/record")
[ -d "$cards" ] && args+=(--cards "$cards")
[ -f "$skill/scripts/scan.py" ] && args+=(--scanner)

echo "The input generator is running; leave this terminal open."
echo "In another terminal, activate your project's venv and open Claude Code in the project:"
echo "  cd $repo && claude"
echo $$ > "$home/generator.pid"
exec python "$tool/tools/inputs/service.py" "${args[@]}"
