#!/usr/bin/env bash
# Start the input generator for your project. Keep it running while you use the
# skill in Claude Code, and stop it with Ctrl-C when you are done.
#
#   dr-greens/start_generator.sh PROJECT KEY_FILE
#
# Run it with your project's venv activated. The generator writes the inputs
# each repair is measured on. Its files are kept in ~/.energy-skill/<project>;
# set ENERGY_SKILL_HOME to use another folder.
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
rm -f "$socket"

args=(--repo-name "$name" --pristine "$repo" --repo "$repo" --key "$key"
      --socket "$socket" --cache "$home/cache"
      --out "$session/inputs" --work "$session/work" --record "$session/record")
cards=$skill/reference/root-causes
[ -d "$cards" ] && args+=(--cards "$cards")
[ -f "$skill/scripts/scan.py" ] && args+=(--scanner)

# The generator locks the root-cause cards until step 1 is finished; unlock them on exit.
trap '[ -d "$cards" ] && chmod -R u+rwX "$cards"' EXIT

echo "The input generator is running; leave this terminal open."
echo "In a second terminal, with your project's venv activated, open Claude Code with:"
echo
echo "  cd $repo"
echo "  ENERGY_INPUTS_SOCKET=$socket claude"
echo
python "$tool/tools/inputs/service.py" "${args[@]}"
