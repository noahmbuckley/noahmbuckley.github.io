#!/bin/bash
# build_apps.sh — re-bundle SDB + Tracker as Shinylive apps for the private/
# section of the website. Run after updates to sdb/app/ or tracker/app/.
#
# Output: ~88-98 MB per app under private/apps/<slug>/
# Time:   ~2-3 min per app (longer on first run; webR runtime cached at
#         ~/Library/Caches/shinylive afterwards).
#
# Requires: R + shinylive package (install: install.packages("shinylive"))

set -euo pipefail

PROJECTS="$HOME/Dropbox/Projects"
PRIVATE="$PROJECTS/me/website/private"
APPS_OUT="$PRIVATE/apps"

echo "▸ Bundling SDB ..."
Rscript -e "shinylive::export(
  appdir = '$PROJECTS/sdb/app',
  destdir = '$APPS_OUT/sdb',
  template_params = list(title = 'FRG Interactive — SDB'))"

echo ""
echo "▸ Staging tracker (data files live outside the appdir) ..."
STAGE="/tmp/tracker_staged"
rm -rf "$STAGE"
mkdir -p "$STAGE/output" "$STAGE/data/inputs"
cp "$PROJECTS/tracker/app/app.R" "$STAGE/app.R"
cp "$PROJECTS/tracker/output"/*.rds "$STAGE/output/" 2>/dev/null || true
cp "$PROJECTS/tracker/data/inputs"/*.rds "$STAGE/data/inputs/" 2>/dev/null || true

# Rewrite TRACKER_ROOT so paths resolve inside the bundle (no `..` traversal)
sed -i.bak \
  -e 's|^TRACKER_ROOT <- .*|TRACKER_ROOT <- "."  # Shinylive build|' \
  "$STAGE/app.R"
# Remove the multi-line (function() ... )() block left over after the sed
# (the two line continuation of the original assignment).
python3 <<'PY'
import re, sys
path = "/tmp/tracker_staged/app.R"
src = open(path).read()
# Drop the leftover lines from the original lambda (idempotent).
src = re.sub(r'^\s*guess <- normalizePath.*?\}\)\(\)\n', '', src, flags=re.M | re.S)
open(path, "w").write(src)
PY
rm -f "$STAGE/app.R.bak"

echo "▸ Bundling tracker ..."
Rscript -e "shinylive::export(
  appdir = '$STAGE',
  destdir = '$APPS_OUT/tracker',
  template_params = list(title = 'Russian Public Opinion Tracker'))"

echo ""
echo "✓ Bundles built:"
du -sh "$APPS_OUT"/sdb "$APPS_OUT"/tracker
echo ""
echo "Reminder: commit and push from website/ to deploy."
