# SPEC — erpk_demo

## 1. App layout

```
erpk_demo/
  hooks.py
  fixtures/                     # exported via hooks `fixtures` (filtered, see §6)
  erpk_demo/
    seed/
      __init__.py               # run(profile, company, abbr=None, demo_password=None)
      common.py                 # idempotent helpers: ensure_doc, ensure_uom, submit_if_draft ...
      masters.py                # company, UOM, groups, items, warehouses, workstations, BOMs
      transactions.py           # opening stock, history, stories
      profiles/
        furniture.py            # all furniture-profile data (dicts/lists only, no logic)
    report/wood_utilisation/    # Script Report
    public/js/quotation.js      # cost + margin on Quotation Item
    public/images/erpkenya-logo.png
    api.py                      # whitelisted get_item_unit_cost(item_code, company)
    install.py                  # after_install: nothing destructive; prints next step
  bin/reset_demo.sh
  tests/
  docs/
```

Entry point:
```
bench --site <site> execute erpk_demo.seed.run \
  --kwargs "{'profile': 'furniture', 'company': 'Tira Studio (Demo)', 'abbr': 'TSD', 'demo_password': '<from user>'}"
```
- `abbr` defaults to initials of company.
- `demo_password` defaults to `frappe.conf.get('erpk_demo_password')`; fail if neither is set.
- Wrap each phase (masters, opening, history, stories, ux) in its own
  `frappe.db.commit()` so a failure mid-way leaves a resumable state; idempotency
  makes re-running safe.
- Log a summary at the end: counts per doctype created vs already present.

## 2. Company and accounting
- Create company from profile: country Kenya, currency KES, chart of accounts
  "Standard", fiscal year covering today and the last 6 months.
- Set as default company in Global Defaults.
- Enable perpetual inventory (default in v16 — verify).
- Stock Settings: valuation method Moving Average; allow negative stock **off**.
- Manufacturing Settings: backflush raw materials based on "BOM"; enable
  "Allow Overtime"; capacity planning on (default) — verify field names in v16.
- Set up 16% VAT as an Item/Sales Taxes template **only for display on invoices**;
  do not mention or configure KRA eTIMS anywhere (ERP Kenya is not an
  authorised eTIMS integrator).

## 3. Manufacturing model (standard ERPNext, configured by seed)
- **Warehouses** (under company root):
  `Maragua Workshop – Raw Materials`, `Maragua Workshop – WIP`,
  `Maragua Workshop – Finished Goods`, `Maragua Workshop – Scrap`,
  `Ngong Road Showroom`, `Redhill Showroom`.
- **Workstations** with hour rates (labour + electricity + overhead rolled up).
- **Operations** linked to default workstations.
- **BOMs** with items, operations ("With Operations" on), and **scrap items**
  (Mango Wood Offcuts in Board Foot, Sawdust in Kg). Default + active, submitted.
  Rate source: Valuation Rate; ensure BOM cost updates after opening stock exists
  (seed opening stock *before* submitting BOMs, or call BOM `update_cost` after).
- **Reorder levels** on raw materials (warehouse = Raw Materials).
- **Bespoke orders**: a bespoke piece is a new Item (code prefix `BSP-`) whose BOM
  is copied from the base piece and scaled. Seed one example. No custom DocType.

## 4. Custom pieces (the only non-standard things)

### 4.1 Quotation: cost and margin while pricing
- Custom fields on **Quotation Item** (and Sales Order Item, same fields, fetched
  through mapping):
  - `erpk_unit_cost` (Currency, read only, label "Est. Unit Cost")
  - `erpk_margin_pct` (Percent, read only, label "Est. Margin %")
- Custom field on **Quotation**: `erpk_total_cost` (Currency, read only),
  `erpk_margin_pct` (Percent, read only), in a section "Costing" after totals.
- `api.get_item_unit_cost(item_code, company)`: returns the default active BOM's
  `total_cost / quantity`; if no BOM, the item's valuation rate; else 0.
- `public/js/quotation.js` (registered via `doctype_js`): on `item_code` and `qty`
  and `rate` change, fetch cost, set row fields, recompute header totals.
  Margin % = (net_amount − cost × qty) / net_amount × 100.
  Colour the margin indicator: < 30% red, 30–45% orange, > 45% green.
- Hide these fields on the print format (internal only).

### 4.2 Wood Utilisation report (Script Report, module ERPK Demo)
Purpose: show progress against "80% waste-free".
- Definition (state it in the report description):
  `utilisation % = (timber issued − timber offcuts returned) / timber issued × 100`
  where "timber" = items in Item Group `Timber` (Board Foot UOM), issued =
  consumed raw material on **Manufacture** Stock Entries, offcuts = scrap rows of
  item `Mango Wood Offcuts` on the same entries. Sawdust shown as a separate
  column (kg) but not in the %.
- Filters: company, from/to date, work order (optional), group by
  (Work Order | Month).
- Columns: Work Order / Month, Item produced, Timber issued (BF), Offcuts (BF),
  Utilisation %, Sawdust (kg), Target %, Variance.
- Target 80% is a report constant via `frappe.conf.get('erpk_utilisation_target', 80)`.
- Chart: line of utilisation % by month with target line (report `get_chart`).

### 4.3 Workspace "Workshop" (fixture)
- **Start here** Custom HTML Block at the top: 5 numbered links, each one sentence:
  1. "See what a dining table really costs" → BOM of DT-6S
  2. "Price a custom order and see the margin" → the open demo Quotation
  3. "Follow a bespoke table from order to delivery" → completed Sales Order
  4. "Check stock at the workshop and both showrooms" → Stock Balance report filtered by company
  5. "See shortages before they reach the floor" → Material Request from reorder
  6. "Track wood utilisation against the 80% goal" → Wood Utilisation report
- Number cards: Open Work Orders; Raw materials below reorder level; Wood
  utilisation this month (%); Sales Orders to deliver.
- Dashboard chart: Wood utilisation by month (from report).
- Shortcuts: Quotation, Sales Order, Work Order, BOM, Stock Entry, Stock Balance.
- Make "Workshop" the default workspace for the demo role profile.
- Verify v16 workspace JSON structure and Custom HTML Block support by reading
  existing workspaces in `apps/erpnext` before writing the fixture.

### 4.4 Branding
- App logo + navbar brand: ERP Kenya logo (`docs/erpkenya-logo.png`).
  Brand colours: navy `#152D5D`, blue `#006EFB`, green `#109A67`.
- A slim persistent banner (via `app_include_js` / `app_include_css`) on every
  desk page: "Demo system by ERP Kenya · sample data · erpkenya.com".
- Print format "ERPK Quotation" and "ERPK Sales Invoice": company logo slot,
  brand colours in the table header, footer with ERP Kenya contact
  (contact@erpkenya.com · +254 757 185189). Do not show cost/margin fields.
- Company letter head: generated from company name; plain, no prospect logo
  (we do not have rights to it).

### 4.5 Demo access
- Role Profile "ERPK Demo User": Sales User, Sales Manager, Stock User, Stock Manager,
  Manufacturing User, Manufacturing Manager, Purchase User, Accounts User.
  **Not** System Manager, not Administrator.
- Demo user: `demo@<site domain>`, full name "Demo User" (never the prospect's
  name), password from `demo_password`, role profile above,
  module profile hiding HR, Payroll, CRM, Projects, Support, Quality, Website,
  Assets, Loan (whatever exists in v16 — verify).
- Desk home → Workshop workspace.

## 5. Non-goals
- No eTIMS, KRA, M-Pesa, POS, webshop, payroll or HR.
- No new DocTypes.
- No real prospect prices, logos or customer names. All figures are labelled sample.

## 6. Fixtures (hooks.py)
Export only records owned by this app, filtered by name or module:
Custom Field (`dt` in Quotation, Quotation Item, Sales Order Item; fieldname like
`erpk_%`), Property Setter (same filter), Workspace (name = "Workshop"),
Number Card + Dashboard Chart (module = ERPK Demo), Print Format (name like `ERPK %`),
Role Profile ("ERPK Demo User"), Module Profile ("ERPK Demo Modules"),
Custom HTML Block (module = ERPK Demo).
Prospect-specific data (company, items, transactions) is **seed**, never fixtures.
