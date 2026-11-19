#!/bin/sh
# Offline checks. Run from anywhere: sh scripts/check.sh
set -e
cd "$(dirname "$0")/.."
python3 plugins/catch-me-up/skills/catch-me-up/scripts/cmu.py selftest
python3 -m unittest discover -s tests -q
python3 -c "import json; json.load(open('.claude-plugin/marketplace.json')); json.load(open('plugins/catch-me-up/.claude-plugin/plugin.json')); print('manifests ok')"
if grep -rn '[–—]' README.md NOTICE CHANGELOG.md plugins/catch-me-up/skills/catch-me-up/SKILL.md; then
  echo "found an em or en dash"; exit 1
fi
echo "all checks passed"
