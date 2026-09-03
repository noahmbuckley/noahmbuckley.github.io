#!/bin/bash
# encrypt_page.sh — passphrase-protect a page under private/ with StatiCrypt
# (client-side AES; the passphrase is typed in the browser, nothing server-side).
# Meant for pages that are "purely for me". Security is deliberately modest:
# the encrypted HTML is public, so a short passphrase can be brute-forced
# offline — fine for non-sensitive material, NOT for anything with personal data.
#
#   ./encrypt_page.sh private/some-page/index.html "silly phrase"
#
# Writes the encrypted file over the docs/ copy only (the source under private/
# stays plain, so rebuilds keep working). Re-run after every rebuild.
set -euo pipefail
SRC="$1"; PASS="$2"
[[ "$SRC" == private/* ]] || { echo "source must be under private/"; exit 1; }
DST="docs/$SRC"
mkdir -p "$(dirname "$DST")"
npx --yes staticrypt "$SRC" -p "$PASS" --short --template-title "$(basename "$(dirname "$SRC")")" \
    --template-instructions "Ask Noah for the passphrase." -d "$(dirname "$DST")" --remember 30
[[ "$(basename "$SRC")" == "index.html" ]] || mv "$(dirname "$DST")/$(basename "$SRC")" "$DST"
grep -q 'name="robots"' "$DST" || sed -i '' 's|<head>|<head><meta name="robots" content="noindex, nofollow">|' "$DST"
echo "encrypted -> $DST  ($(wc -c <"$DST") bytes)"
