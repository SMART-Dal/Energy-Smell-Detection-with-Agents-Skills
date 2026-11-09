#!/usr/bin/env bash
# Open Claude Code in your project, with the input generator running beside it.
#
#   dr-greens/start.sh PROJECT KEY_FILE [CLAUDE OPTIONS]
#
# Run it with your project's venv activated. The generator writes the inputs
# each repair is measured on, and stops when you leave Claude Code. Its files
# are kept in ~/.energy-skill/<project>; set ENERGY_SKILL_HOME to use another folder.
set -euo pipefail

tool=$(cd "$(dirname "$0")" && pwd)
[ -f "$tool/tools/inputs/service.py" ] || { echo "Run start.sh from the unzipped dr-greens folder; do not copy it."; exit 1; }
repo=$(cd "$1" && pwd)
key=$(cd "$(dirname "$2")" && pwd)/$(basename "$2")
shift 2
name=$(basename "$repo")
skill=$(ls -d "$repo"/.claude/skills/energy-* 2>/dev/null | head -1 || true)
[ -n "$skill" ] || { echo "No skill in $repo/.claude/skills: copy one there first."; exit 1; }
[ -s "$key" ] || { echo "No key in $key: save your OpenRouter key there."; exit 1; }

home=${ENERGY_SKILL_HOME:-$HOME/.energy-skill}/$name
session=$home/sessions/$(date +%Y%m%d-%H%M%S)
socket=${XDG_RUNTIME_DIR:-/tmp}/energy-inputs-$name.sock    # a socket path is limited to 108 characters
mkdir -p "$session"

args=(--repo-name "$name" --pristine "$repo" --repo "$repo" --key "$key"
      --socket "$socket" --cache "$home/cache"
      --out "$session/inputs" --work "$session/work" --record "$session/record")
cards=$skill/reference/root-causes
[ -d "$cards" ] && args+=(--cards "$cards")
[ -f "$skill/scripts/scan.py" ] && args+=(--scanner)

# Start the generator, and stop it (unlocking the root-cause cards) when Claude Code exits.
rm -f "$socket"
python "$tool/tools/inputs/service.py" "${args[@]}" > "$session/generator.log" 2>&1 &
generator=$!
trap 'kill $generator 2>/dev/null; [ -d "$cards" ] && chmod -R u+rwX "$cards"' EXIT
for _ in $(seq 60); do
  [ -S "$socket" ] && break
  kill -0 $generator 2>/dev/null || { echo "The input generator did not start:"; tail -3 "$session/generator.log"; exit 1; }
  sleep 1
done

cd "$repo"
ENERGY_INPUTS_SOCKET=$socket claude "$@"
