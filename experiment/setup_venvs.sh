#!/usr/bin/env bash
# Builds one venv per repo and saves it as venvs/<repo>.tar. Every run unpacks
# a fresh copy at $RUN/venv, so whatever one agent installs is gone for the next.
#
#   ./setup_venvs.sh                  every repo in repos.tsv
#   ./setup_venvs.sh gedcom feast     just these
set -uo pipefail
source "$(dirname "$0")/config.sh"
mkdir -p "$EXP/venvs" "$EXP/logs" "$RUN"

repos=("$@")
[ ${#repos[@]} -eq 0 ] && mapfile -t repos < <(cut -f1 "$HARNESS/repos.tsv")

for repo in "${repos[@]}"; do
  log=$EXP/logs/venv-$repo.log
  echo "== $repo"
  rm -rf "$RUN/venv"
  python3 -m venv "$RUN/venv" > "$log" 2>&1
  py=$RUN/venv/bin/python
  # Our tools (scanner, verifier, meter), common libraries and the repo's own
  # requirements, resolved together in one pip call; see lib/repo_deps.py.
  "$py" -m pip install -q --upgrade pip >> "$log" 2>&1
  "$py" "$HARNESS/lib/repo_deps.py" "$EXP/pristine/$repo" \
    -r "$PROJECT/requirements.txt" $COMMON_PACKAGES >> "$log" 2>&1
  tar -cf "$EXP/venvs/$repo.tar" -C "$RUN" venv
  echo "  $("$py" -m pip freeze | wc -l) packages; log: $log"
  grep -E '^(WARNING|install:|undeclared:|pip check)' "$log" | sed "s/^/  /"
  rm -rf "$RUN/venv"
done
