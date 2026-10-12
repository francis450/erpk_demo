# ERPK Demo

Turns a fresh ERPNext v16 site into a believable, resettable demo for one prospect.
The first profile is **furniture**: a solid-wood maker with a workshop and two showrooms.
All figures are sample data.

What the demo shows:

- **True cost of every piece.** BOMs with materials, labour by workstation, and scrap credit.
  Quotations show estimated unit cost and margin live.
- **Stock at the workshop and each showroom.** Reorder levels, plus a fabric shortage that shows up
  before it reaches the floor.
- **A custom order end to end.** Quote → sales order → work order → job cards → manufacture →
  delivery → invoice → payments.
- **Wood utilisation against an 80% waste-free target.** A script report with a monthly trend.

## Install

```bash
bench get-app <private repo url> --branch main
bench new-site <name>.demo.erpkenya.com --install-app erpnext --install-app erpk_demo
bench --site <site> set-config erpk_demo_password '<demo password>'
bench --site <site> set-config mute_emails 1 --parse
```

Fixtures (custom fields, workspace, number cards, chart, print formats, role and module
profiles) load on install.

## Seed

```bash
bench --site <site> execute erpk_demo.seed.run \
  --kwargs "{'profile': 'furniture', 'company': '<Company>', 'abbr': '<ABBR>'}"
```

- If the company already exists (for example from the setup wizard), the seed uses it and its abbreviation.
- Re-running is safe: every record is keyed, and the second run creates nothing.
- The run ends with a summary (created / already present) and the final-state checks.
- Phases: `masters`, `opening`, `history`, `stories`, `ux`. Run a subset with `'phases': [...]`.
- The demo user is `demo@<site>`, with the password above. They land on the **Workshop** workspace.

## Reset

Reset only works for site names that contain `demo`. Every script refuses other sites.

```bash
apps/erpk_demo/bin/make_golden.sh <site> --yes   # after seeding and a manual check
apps/erpk_demo/bin/reset_demo.sh  <site> --yes   # restore golden DB + files
```

For unattended runs (cron), provide the MariaDB root password in `ERPK_DB_ROOT_PASSWORD`, or as
`root_password` in the bench config. Each reset is logged to `logs/erpk_demo_reset.log`.

## Deploy (short form)

1. Production bench on the same ERPNext v16 minor version, with wildcard DNS
   `*.demo.erpkenya.com` and `bench config dns_multitenant on`.
2. Run Install and Seed (above), then `bench setup nginx` and the TLS certificate.
3. Disable the scheduler: `bench --site <site> disable-scheduler`.
   Re-apply the hardening if needed: `bench --site <site> execute erpk_demo.tools.harden`.
4. Run `make_golden.sh`. Add a nightly cron at 02:30 EAT: `reset_demo.sh <site> --yes`.
5. Send the prospect the URL and the demo user's login. Never send the Administrator login.

Check a site: `bench --site <site> execute erpk_demo.tools.status`.
Full detail is in `docs/DEPLOY.md`. Departures from the spec are in `docs/DEVIATIONS.md`.

## Develop

- Prospect data lives only in `erpk_demo/seed/profiles/<profile>.py`.
- Regenerate fixtures after changing `erpk_demo/setup/fixture_records.py`:
  `bench --site <dev site> execute erpk_demo.setup.fixture_records.build && bench --site <dev site> export-fixtures --app erpk_demo`.
- Tests (on a seeded throwaway site): `bench --site <test site> run-tests --app erpk_demo`.

MIT licence.
