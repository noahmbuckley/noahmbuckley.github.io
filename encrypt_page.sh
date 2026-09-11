#!/bin/bash
# encrypt_page.sh — passphrase-protect a page under resources/ with StatiCrypt
# (client-side AES; the passphrase is typed in the browser, nothing server-side).
# Meant for pages that are "purely for me". Security is deliberately modest:
# the encrypted HTML is public, so a short passphrase can be brute-forced
# offline — fine for non-sensitive material, NOT for anything with personal data.
#
#   ./encrypt_page.sh resources/some-page/index.html "silly phrase"
#
# Writes the encrypted file over the docs/ copy only (the source under resources/
# stays plain, so rebuilds keep working). That also means a full `quarto render`
# of the site copies the PLAIN source back over it: re-run this after every full
# render, not just after rebuilding the page. (The teaching decks avoid this by
# keeping the encrypted copy in the source tree too; see resources/README.md.)
set -euo pipefail
SRC="$1"; PASS="$2"
[[ "$SRC" == resources/* ]] || { echo "source must be under resources/"; exit 1; }
DST="docs/$SRC"
mkdir -p "$(dirname "$DST")"
npx --yes staticrypt "$SRC" -p "$PASS" --short --template-title "$(basename "$(dirname "$SRC")")" \
    --template-instructions "Ask Noah for the passphrase." -d "$(dirname "$DST")" --remember 30
[[ "$(basename "$SRC")" == "index.html" ]] || mv "$(dirname "$DST")/$(basename "$SRC")" "$DST"
grep -q 'name="robots"' "$DST" || sed -i '' 's|<head>|<head><meta name="robots" content="noindex, nofollow">|' "$DST"
echo "encrypted -> $DST  ($(wc -c <"$DST") bytes)"
