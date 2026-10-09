# DEPLOY — production demo sites

Target: one production bench on the ERP Kenya VPS hosting one site per prospect,
e.g. `tira.demo.erpkenya.com`. Sites are disposable; the app repo is the source
of truth.

## 1. Before deploying (local)
- All items in `ACCEPTANCE.md` pass on the local v16 site.
- App pushed to a private Git repo (ask the user for the remote; do not create
  public repos).
- `README.md` documents the three commands: install, seed, reset.

## 2. Server prerequisites (verify, do not assume)
- Production bench on ERPNext **v16** (same minor version as local; check
  `bench version`). Python/Node/MariaDB/Redis versions as required by v16 — read
  the v16 installation docs or `apps/frappe/pyproject.toml`, don't guess.
- Wildcard DNS `*.demo.erpkenya.com` → VPS IP (user does this at the registrar).
- Bench in production mode (supervisor + nginx); `dns_multitenant` on:
  `bench config dns_multitenant on`.

## 3. Create a prospect site
```bash
bench get-app <private repo url> --branch main          # first time only
bench new-site tira.demo.erpkenya.com \
  --admin-password '<strong, stored in password manager>' \
  --install-app erpnext --install-app erpk_demo
bench --site tira.demo.erpkenya.com set-config erpk_demo_password '<demo pw>'
bench --site tira.demo.erpkenya.com set-config mute_emails 1
bench --site tira.demo.erpkenya.com set-config erpk_utilisation_target 80
bench --site tira.demo.erpkenya.com execute erpk_demo.seed.run \
  --kwargs "{'profile':'furniture','company':'Tira Studio (Demo)','abbr':'TSD'}"
bench setup nginx && sudo service nginx reload
sudo -H bench setup lets-encrypt tira.demo.erpkenya.com   # or wildcard cert via certbot DNS
```

## 4. Hardening (seed or a `harden` helper applies these; verify each)
- `mute_emails = 1` (no outbound mail at all).
- System Settings: disable sign-up (`disable_user_signup`/website sign-up off —
  verify v16 field), session expiry 12h, password policy on, login attempts
  limited, two-factor **off** for the demo user only.
- Website: home page redirects to `/login`; `robots.txt` disallow all; add
  `X-Robots-Tag: noindex` via nginx include for `*.demo.erpkenya.com`.
- Disable scheduler jobs that send or sync anything external; keep the reorder
  job only if needed (story 3 is seeded, so the scheduler can be **disabled**:
  `bench --site X disable-scheduler`).
- Administrator password never shared; demo user is the only credential sent to
  the prospect.
- Backups of demo sites are not business data; exclude from offsite backup jobs.

## 5. Golden backup and nightly reset
After seeding and a manual check:
```bash
bench --site tira.demo.erpkenya.com backup --with-files
# copy the produced files to sites/tira.demo.erpkenya.com/private/golden/
```
`bin/reset_demo.sh <site>`:
- Refuse to run unless `<site>` matches `*.demo.erpkenya.com` (or contains `demo`
  for local testing). Print the site and require `--yes` flag.
- Restore DB + files from `private/golden/` with
  `bench --site <site> restore ... --with-public-files ... --with-private-files ...`
  then re-apply `set-config` keys (restore keeps site_config, verify) and
  `bench --site <site> clear-cache`.
- Log to `logs/erpk_demo_reset.log`.

Cron (bench user), 02:30 EAT nightly:
```
30 2 * * * /home/frappe/frappe-bench/apps/erpk_demo/bin/reset_demo.sh tira.demo.erpkenya.com --yes
```
Note: this wipes whatever the prospect entered that day. If the prospect is
actively evaluating, ask the user whether to pause the cron for that site.

## 6. Share with the prospect
Send: site URL, demo username/password, and the one-line instruction
"Start on the Workshop page and follow the six links in order."
Never send the Administrator login.

## 7. Retire a site
When a lead closes or goes cold for 30 days, ask the user, then:
`bench drop-site tira.demo.erpkenya.com --archived-sites-path ~/archived-demos`.
