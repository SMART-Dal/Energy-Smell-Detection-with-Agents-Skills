#!/usr/bin/env bash
# Start the input generator for your project. Keep it running while you use the
# skill in Claude Code, and stop it with Ctrl-C when you are done.
#
#   dr-greens/start_generator.sh PROJECT KEY_FILE
#
# Run it with your project's venv activated. While it runs, Claude Code sessions
# opened in the project (`cd PROJECT && claude`) are connected to it and use that
# venv: it adds them to PROJECT/.claude/settings.local.json and restores that
# file when it stops. Its own files are kept in ~/.energy-skill/<project>; set
# ENERGY_SKILL_HOME to use another folder.
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

# Point Claude Code sessions in the project at the generator and the venv.
settings=$repo/.claude/settings.local.json
[ -f "$settings" ] && cp "$settings" "$session/settings.local.json.backup"
python - "$settings" "$socket" <<'PY'
import json, os, sys
path, socket = sys.argv[1], sys.argv[2]
settings = json.load(open(path)) if os.path.exists(path) else {}
env = settings.setdefault("env", {})
env["ENERGY_INPUTS_SOCKET"] = socket
if os.environ.get("VIRTUAL_ENV"):
    env["VIRTUAL_ENV"] = os.environ["VIRTUAL_ENV"]
    env["PATH"] = os.environ["PATH"]
json.dump(settings, open(path, "w"), indent=2)
PY

# On exit: restore the settings file, and unlock the root-cause cards the generator locks until step 1.
restore() {
  if [ -f "$session/settings.local.json.backup" ]; then cp "$session/settings.local.json.backup" "$settings"
  else rm -f "$settings"; fi
  [ -d "$cards" ] && chmod -R u+rwX "$cards"
}
trap restore EXIT

echo "The input generator is running; leave this terminal open."
echo "Open Claude Code in your project as usual (cd $repo && claude)."
echo "Stop the generator with Ctrl-C when you are done."
echo
python "$tool/tools/inputs/service.py" "${args[@]}"
