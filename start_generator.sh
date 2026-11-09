#!/usr/bin/env bash
# Start the input generator for a project, and keep it running while you use the
# skill in Claude Code. It stops when you press Ctrl-C or close this terminal.
#
#   dr-greens/start_generator.sh PROJECT KEY_FILE
#
# Run it with the project's venv activated. Claude Code finds the generator
# through ENERGY_INPUTS_SOCKET="$HOME/.energy-skill/inputs.sock" (see the README).
# One project at a time.
set -euo pipefail

tool=$(cd "$(dirname "$0")" && pwd)
project=$(cd "$1" && pwd)
name=$(basename "$project")
skill=$(ls -d "$project"/.claude/skills/energy-* | head -1)
data=$HOME/.energy-skill/$name/$(date +%Y%m%d-%H%M%S)      # this session's inputs and step records

args=(--repo-name "$name" --pristine "$project" --repo "$project" --key "$(realpath "$2")"
      --socket "$HOME/.energy-skill/inputs.sock" --cache "$HOME/.energy-skill/cache"
      --out "$data/inputs" --work "$data/work" --record "$data/record")
# The cards stay closed until step 1 is finished; the full skill also checks that its rules were run.
[ -d "$skill/reference/root-causes" ] && args+=(--cards "$skill/reference/root-causes")
[ -f "$skill/scripts/scan.py" ] && args+=(--scanner)

mkdir -p "$data"
rm -f "$HOME/.energy-skill/inputs.sock"
echo "+ python tools/inputs/service.py ${args[*]}"
exec python "$tool/tools/inputs/service.py" "${args[@]}"
