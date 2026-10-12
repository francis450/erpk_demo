#!/usr/bin/env bash
# Restore a demo site to its golden state (DB + public + private files).
#   bin/reset_demo.sh <site> --yes
# Golden files live in sites/<site>/private/golden/ (see bin/make_golden.sh).
# MariaDB root password: $ERPK_DB_ROOT_PASSWORD, else bench's root_password config.
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/_guard.sh"
erpk_guard "${1:-}" "${2:-}"
SITE="$1"
GOLDEN="$SITE_DIR/private/golden"
LOG="$BENCH/logs/erpk_demo_reset.log"
mkdir -p "$BENCH/logs"
exec > >(tee -a "$LOG") 2>&1
echo "== $(date -Is) reset $SITE"

latest() { ls -1t "$GOLDEN"/$1 2>/dev/null | head -n 1 || true; }
DB="$(latest '*-database.sql.gz')"
PUB="$(latest '*-files.tar')"
PRIV="$(latest '*-private-files.tar')"
if [[ -z "$DB" ]]; then
	echo "no golden database backup in $GOLDEN; run bin/make_golden.sh first" >&2
	exit 6
fi

# Site config keys the demo relies on, re-applied after restore
cd "$BENCH"
keys=(erpk_demo_password mute_emails erpk_utilisation_target)
declare -A saved
for k in "${keys[@]}"; do
	saved[$k]="$(env/bin/python -c "import json,sys;print(json.load(open('$SITE_DIR/site_config.json')).get('$k',''))")"
done

args=(--force)
[[ -n "$PUB" ]] && args+=(--with-public-files "$PUB")
[[ -n "$PRIV" ]] && args+=(--with-private-files "$PRIV")
[[ -n "${ERPK_DB_ROOT_PASSWORD:-}" ]] && args+=(--db-root-password "$ERPK_DB_ROOT_PASSWORD")

echo "restoring $DB"
bench --site "$SITE" restore "$DB" "${args[@]}"

for k in "${keys[@]}"; do
	if [[ -n "${saved[$k]}" ]]; then
		bench --site "$SITE" set-config "$k" "${saved[$k]}" --parse 2>/dev/null \
			|| bench --site "$SITE" set-config "$k" "${saved[$k]}"
	fi
done
bench --site "$SITE" set-config mute_emails 1 --parse
bench --site "$SITE" clear-cache
echo "== $(date -Is) reset done"
