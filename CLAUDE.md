# erpk_demo — ERP Kenya prospect demo app

A thin Frappe app that turns a fresh ERPNext v16 site into a believable, resettable
demo for a specific prospect. First profile: **furniture** (prospect: Tira Studio,
a Nairobi maker of solid mango wood furniture with a workshop in Maragua and
showrooms on Ngong Road and at Redhill).

The demo must prove three promises made to the prospect in writing:
1. See the true cost of every piece (wood, fabric, hardware, labour).
2. Track raw material at the workshop and finished pieces at each showroom, and see
   shortages coming before they hit the floor.
3. Take a custom order from quote to production to delivery.

Plus one differentiator: track wood utilisation against the prospect's
"80% waste-free workshop" goal.

## Read these first, in order
1. `docs/SPEC.md` — what the app contains and how each part works
2. `docs/SEED_DATA.md` — every record the furniture profile creates
3. `docs/ACCEPTANCE.md` — the checks that define "done"
4. `docs/DEPLOY.md` — production deployment, reset and hardening

## Ground rules
- **Standard ERPNext first.** Only build what SPEC.md lists as custom. If a standard
  feature covers it, configure it via the seed or fixtures; do not write a DocType.
- **Verify against installed v16 source, never memory.** Before using any ERPNext/Frappe
  API, field name, or method, grep the installed apps
  (`apps/erpnext`, `apps/frappe`) to confirm it exists in this version. v16 renamed
  and moved things; assume nothing from v14/v15 tutorials. If a SPEC field name
  is wrong for v16, use the real one and note it in `docs/DEVIATIONS.md`.
- **Seed must be idempotent.** Running `seed.run` twice on the same site must not
  duplicate or fail. Check existence before insert; key everything on stable names.
- **Profile + company are parameters.** Nothing in code may hard-code "Tira".
  All prospect-specific strings live in `erpk_demo/seed/profiles/furniture.py`
  (or a JSON next to it) and the `company` argument.
- **Destructive commands need explicit approval.** Never run `bench drop-site`,
  `bench --site X restore`, `reinstall`, or raw `DELETE`/`TRUNCATE` without
  asking the user first, and never against any site whose name does not
  contain `demo`. `bin/reset_demo.sh` must enforce the same guard.
- **No outbound email from demo sites.** `mute_emails` stays on (see DEPLOY.md).
- **Commit at each milestone** below with a clear message. Keep the app installable
  at every commit.

## Environment
- Local bench with ERPNext **v16** and one site already created by the user. Ask
  the user for the bench path and site name if not obvious from `sites/`.
- Create the app with `bench new-app erpk_demo` (module: `ERPK Demo`,
  publisher: ERP Kenya, licence: MIT), then `bench --site <site> install-app erpk_demo`.

## Build order (milestones)
1. Scaffold app, hooks, fixtures config, empty seed entrypoint. Installs cleanly.
2. Seed: masters (company, UOMs, item groups, items, warehouses, workstations,
   operations, BOMs, prices, customers, suppliers). Idempotent.
3. Seed: opening stock + historical transactions (backdated work orders for the
   utilisation trend) + the three demo stories.
4. Custom pieces: Quotation cost/margin fields + client script; Wood Utilisation
   script report; workspace with number cards, chart and "Start here" block;
   branded print formats; demo role profile + demo user.
5. Reset tooling (`bin/reset_demo.sh`), golden backup, `bench execute` helpers.
6. Tests + run every item in `docs/ACCEPTANCE.md`; fix until all pass.
7. Write `README.md` (install, seed, reset, deploy in short form) and
   `docs/DEVIATIONS.md` (anything that differs from the spec, and why).

Report to the user after milestones 3, 4 and 6 with what was done and what
the walkthrough looks like (screenshots via Playwright if available).
