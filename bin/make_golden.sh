#!/usr/bin/env bash
# Take the golden backup a demo site is reset to. Run after seeding and a manual check.
#   bin/make_golden.sh <site> --yes
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_guard.sh"
erpk_guard "${1:-}" "${2:-}"
SITE="$1"
GOLDEN="$SITE_DIR/private/golden"
mkdir -p "$GOLDEN"
cd "$BENCH"
bench --site "$SITE" backup --with-files --backup-path "$GOLDEN"
# keep only the newest set
for pat in '*-database.sql.gz' '*-files.tar' '*-private-files.tar' '*-site_config_backup.json'; do
	ls -1t "$GOLDEN"/$pat 2>/dev/null | tail -n +2 | xargs -r rm -f
done
ls -l "$GOLDEN"
