#!/usr/bin/env bash
# Clone the experiment's repositories into $EXP/pristine.
#
#   ./setup_repos.sh               every repo in repos.tsv, at the commit it lists
#   ./setup_repos.sh CSV N         choose the first N repos of a CSV (column `name` =
#                                  owner/repo), clone their default branch, and write
#                                  repos.tsv (name, owner/repo, commit, .py files)
#
# The first form is what a replication runs; the second is how repos.tsv was made.
set -uo pipefail
source "$(dirname "$0")/config.sh"
mkdir -p "$EXP/pristine"

if [ $# -eq 0 ]; then
  while IFS=$'\t' read -r name full sha _; do
    dir=$EXP/pristine/$name
    if [ "$(git -C "$dir" rev-parse HEAD 2>/dev/null)" = "$sha" ]; then
      echo "$name: already at $sha"
      continue
    fi
    rm -rf "$dir"
    git init -q "$dir" && git -C "$dir" remote add origin "https://github.com/$full.git" \
      && git -C "$dir" fetch -q --depth 1 origin "$sha" && git -C "$dir" checkout -q FETCH_HEAD \
      && echo "$name: $sha" || echo "$name: FAILED to fetch $full at $sha"
  done < "$REPOS_FILE"
  exit 0
fi

CSV=$1
N=${2:-10}
python3 -c "
import csv, sys
rows = list(csv.DictReader(open(sys.argv[1])))[:int(sys.argv[2])]
print('\n'.join(r['name'] for r in rows))" "$CSV" "$N" |
while read -r full; do
  name=${full#*/}
  if [ ! -d "$EXP/pristine/$name/.git" ]; then
    git clone -q --depth 1 "https://github.com/$full.git" "$EXP/pristine/$name" || continue
  fi
  sha=$(git -C "$EXP/pristine/$name" rev-parse HEAD)
  py=$(find "$EXP/pristine/$name" -name '*.py' -not -path '*/.git/*' | wc -l)
  printf '%s\t%s\t%s\t%s\n' "$name" "$full" "$sha" "$py"
done > "$REPOS_FILE"
cat "$REPOS_FILE"
