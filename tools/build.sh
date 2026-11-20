#!/bin/sh
# Regenerate templates and patterns, validate them, and rebuild the zips.
# Needs Python 3 and Node 20+ (run "npm install" in tools/ once).
set -e
cd "$(dirname "$0")/.."
python3 tools/gen_theme.py
node tools/validate.mjs cet-ece/templates/*.html cet-ece/parts/*.html cet-ece/patterns/*.php
mkdir -p dist && rm -f dist/*.zip
zip -qr dist/cet-ece.zip cet-ece
zip -qr dist/cet-ece-core.zip cet-ece-core
echo "Built dist/cet-ece.zip and dist/cet-ece-core.zip"
