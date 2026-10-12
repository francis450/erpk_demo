# Shared by the erpk_demo scripts. Sourced, not executed.
# Usage: erpk_guard <site> <yes-flag>; sets BENCH and SITE_DIR.

erpk_guard() {
	local site="$1" yes="$2"
	if [[ -z "$site" ]]; then
		echo "usage: $(basename "$0") <site> --yes" >&2
		exit 2
	fi
	# Only demo sites: *.demo.erpkenya.com in production, any name containing "demo" locally.
	if [[ "$site" != *demo* ]]; then
		echo "refusing: site '$site' does not contain 'demo'" >&2
		exit 3
	fi
	BENCH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
	SITE_DIR="$BENCH/sites/$site"
	if [[ ! -d "$SITE_DIR" ]]; then
		echo "refusing: no site directory $SITE_DIR" >&2
		exit 4
	fi
	echo "site: $site"
	if [[ "$yes" != "--yes" ]]; then
		echo "refusing: pass --yes to confirm" >&2
		exit 5
	fi
}
