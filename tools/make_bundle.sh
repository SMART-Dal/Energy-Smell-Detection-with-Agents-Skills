#!/usr/bin/env bash
# Build dr-greens.zip, the download for users of the skills: the three skills,
# the input generator, apply.sh and the README.
#
#   tools/make_bundle.sh        writes dr-greens.zip in the repository root
set -euo pipefail
cd "$(dirname "$0")/.."

stage=$(mktemp -d)
out=$stage/dr-greens
mkdir -p "$out/skills" "$out/tools/inputs"

cp -r dist/core dist/core+tax dist/full "$out/skills/"
cp -r src "$out/src"
cp tools/review.py "$out/tools/"
cp tools/inputs/service.py tools/inputs/generate.py tools/inputs/steps.py "$out/tools/inputs/"
cp start_inputs.sh apply.sh requirements-skill.txt README.md "$out/"
find "$out" -name __pycache__ -prune -exec rm -rf {} +

rm -f dr-greens.zip
(cd "$stage" && python3 -m zipfile -c "$OLDPWD/dr-greens.zip" dr-greens)
rm -rf "$stage"
echo "wrote dr-greens.zip ($(du -h dr-greens.zip | cut -f1))"
