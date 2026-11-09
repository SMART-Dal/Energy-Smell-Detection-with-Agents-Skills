#!/usr/bin/env bash
# Start the input generator for a repository that has one of the skills installed.
# Keep it running while you use the skill in Claude Code; stop it with Ctrl-C.
#
#   ./start_inputs.sh REPO OPENROUTER_KEY_FILE
#
# Run it with the repository's venv activated: the generator runs the
# repository's code to check each input it writes.
set -euo pipefail

tool=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$1" && pwd)
key=$2
name=$(basename "$repo")
skill=$(ls -d "$repo"/.claude/skills/energy-* | head -1)

# Everything the generator keeps for this repository: the socket Claude Code
# connects to, an inputs cache, and one folder per session.
home=$HOME/.energy-skill/$name
session=$home/sessions/$(date +%Y%m%d-%H%M%S)
mkdir -p "$session"

args=(--repo-name "$name" --pristine "$repo" --repo "$repo" --key "$key"
      --socket "$home/inputs.sock" --cache "$home/cache"
      --out "$session/inputs" --work "$session/work" --record "$session/record")
cards=$skill/reference/root-causes
[ -d "$cards" ] && args+=(--cards "$cards")
[ -f "$skill/scripts/scan.py" ] && args+=(--scanner)

# The generator locks the root-cause cards until step 1 is finished; unlock them on exit.
trap '[ -d "$cards" ] && chmod -R u+rwX "$cards"' EXIT

echo "Input generator running. In another terminal, with the same venv activated:"
echo "  cd $repo"
echo "  export ENERGY_INPUTS_SOCKET=$home/inputs.sock"
echo "  claude"
python "$tool/tools/inputs/service.py" "${args[@]}"
