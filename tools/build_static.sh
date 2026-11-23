#!/bin/sh
# Build a static copy of the site (theme, plugin and the demo content in
# playground/data/) as plain HTML, for GitHub Pages or any web host.
#
#   sh tools/build_static.sh [out-dir] [public-url]
#   sh tools/build_static.sh _site https://jim79.github.io/cet-ece-wp
#
# Needs Node 24+, wget and Python 3. It starts WordPress in Playground,
# loads the content, saves every page with wget, then tidies the files.
# The GitHub Actions workflow .github/workflows/pages.yml runs this on every
# push to main.
#
# Offline or behind a firewall that blocks wordpress.org: set WP_DIR to an
# unpacked WordPress whose wp-content/plugins holds secure-custom-fields and
# sqlite-database-integration. Use a fresh copy each time: Playground writes
# its database into it.
set -eu
cd "$(dirname "$0")/.."
ROOT=$(pwd)
OUT=${1:-_site}
PUBLIC=${2:-https://jim79.github.io/cet-ece-wp}
PORT=${PORT:-9500}
BASE="http://127.0.0.1:$PORT"

if [ -e "$OUT" ] && [ -n "$(ls -A "$OUT" 2>/dev/null)" ]; then
	echo "$OUT is not empty: choose a new folder" >&2
	exit 1
fi
mkdir -p "$OUT"
WORK=$(mktemp -d)

if [ -n "${WP_DIR:-}" ]; then
	python3 tools/static_site.py blueprint "$WORK/blueprint.json" --local
	set -- --wordpress-install-mode=install-from-existing-files --mount-before-install="$WP_DIR:/wordpress"
else
	python3 tools/static_site.py blueprint "$WORK/blueprint.json"
	set --
fi

echo "Starting WordPress and loading the content (several minutes)..."
npx -y @wp-playground/cli@3.1.65 server --port="$PORT" --blueprint="$WORK/blueprint.json" \
	--mount="$ROOT/cet-ece-core:/wordpress/wp-content/plugins/cet-ece-core" \
	--mount="$ROOT/cet-ece:/wordpress/wp-content/themes/cet-ece" \
	--mount="$ROOT/playground:/demo" \
	"$@" > "$WORK/server.log" 2>&1 &
PID=$!
trap 'kill $PID 2>/dev/null || true' EXIT INT TERM

i=0
until grep -q "Ready!" "$WORK/server.log"; do
	if ! kill -0 "$PID" 2>/dev/null; then
		grep -v "npm warn" "$WORK/server.log" | tail -40 >&2
		echo "WordPress did not start." >&2
		exit 1
	fi
	i=$((i + 1))
	if [ "$i" -gt 2400 ]; then
		echo "Timed out waiting for WordPress." >&2
		exit 1
	fi
	sleep 1
done

echo "Saving the pages..."
python3 tools/static_site.py urls "$BASE" > "$WORK/urls.txt"
echo "$(wc -l < "$WORK/urls.txt") pages in the sitemap"
# wget exits non-zero when any single request fails (8: a page returned an
# error, 4: a request timed out). The check below decides whether the copy is usable.
code=0
wget --no-verbose --recursive --level=inf --page-requisites --adjust-extension --convert-links \
	--restrict-file-names=windows --no-host-directories -e robots=off --tries=3 --timeout=120 \
	--reject-regex '/(wp-admin|wp-login\.php|xmlrpc\.php|wp-json|feed)(/|$|\?)|/comments/feed/|[?&]p=[0-9]+|//127\.0\.0\.1/' \
	--directory-prefix="$OUT" --input-file="$WORK/urls.txt" > "$WORK/wget.log" 2>&1 || code=$?
if [ "$code" -ne 0 ]; then
	echo "wget finished with code $code; requests that failed:"
	grep -iE "error|failed|timed out" "$WORK/wget.log" | head -20 || true
fi
wget --quiet --content-on-error -O "$OUT/404.html" "$BASE/this-page-does-not-exist/" || true

missing=0
for page in index.html faculty/index.html labs/index.html research/publications/index.html academics/obe/index.html; do
	if [ ! -s "$OUT/$page" ]; then
		echo "Missing from the copy: $page" >&2
		missing=1
	fi
done
if [ "$missing" -ne 0 ]; then
	echo "Last lines of the WordPress log:" >&2
	grep -v "npm warn" "$WORK/server.log" | tail -30 >&2
	exit 1
fi

python3 tools/static_site.py fix "$OUT" "$BASE" "$PUBLIC"
echo "Static copy in $OUT ($(find "$OUT" -name '*.html' | wc -l) pages), for $PUBLIC"
