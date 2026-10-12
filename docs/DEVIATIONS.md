# Deviations from the spec

These are the places where the build differs from SPEC.md and SEED_DATA.md, and why. Each item was
checked against the installed ERPNext/Frappe 16.50 source.

## v16 renames and moves

| Spec says | v16 reality | What we did |
| --- | --- | --- |
| BOM **scrap items** | Table `secondary_items` (BOM Secondary Item), `secondary_item_type = Scrap` | Scrap rows are secondary items with `valuation_type = Valuation Rate`, so their value is subtracted from BOM total cost as the spec intends. Stock Entry rows carry `secondary_item_type`. |
| Workstation hour rate | `hour_rate` is read-only, computed from the `workstation_costs` table (Workstation Operating Component rows) | Each hour rate is split into Wages, Electricity and Rent components that add up to the spec rate, so the costing story shows the breakdown. |
| Manufacturing Settings default WIP / FG / scrap warehouses | These fields moved to **Company** (`default_wip_warehouse`, `default_fg_warehouse`, `default_scrap_warehouse`) | Set on Company. |
| Operating cost posting | Needs an account per operating component, falling back to Company `default_operating_cost_account` | If that account is empty, the seed sets it to *Expenses Included In Valuation* (the standard absorption account). |
| User `role_profile_name` | Deprecated; v16 uses the `role_profiles` table | The demo user gets the role profile through `role_profiles`. |
| Custom HTML Block `module` (for the fixture filter) | The doctype has no `module` field | The fixture filters on `name like "ERPK %"`. The block is named `ERPK Start Here`. |
| Desk routes `/app/...` | v16 uses `/desk/...` | Start-here links use `/desk/...` routes. |
| Workspace sidebar | Modules without a Sidebar document get a computed sidebar | "Workshop" is a public workspace in module *ERPK Demo*. It appears in that module's computed sidebar, and the demo user's `default_workspace` lands them on it. No separate sidebar or desktop-icon records are needed. |

## Data and behaviour

- **One work order per piece in the history.** SEED_DATA §11 lists 11 item×qty lines, but §13 asks for
  ≥ 14 completed work orders. The seed makes one work order per piece: 19 history work orders plus the
  bespoke one, 20 completed in total. The utilisation trend lands on the spec targets:
  ~72 / 75 / 78 / 81% and 79% for the current month.
- **Fabric bought once in month −2.** The sofa built in month −2 consumes all 14 m of opening fabric.
  A Purchase Invoice (with stock update) for 14 m from the fabric supplier, dated just before that build,
  brings the stock back to 14 m. That keeps story 3's "14 m on hand" true.
- **Shortage material request is a draft.** ERPNext's reorder job (`erpnext.stock.reorder_item.reorder_item`)
  submits its request. A submitted request counts in projected qty (14 + 80 − 28 = 66), which hides the
  shortage the story is meant to show. So the seed creates the request in **Draft**, sized the way the
  reorder job sizes it (80 m). Stock Projected Qty then shows −14 m against the sofa work order.
  `auto_indent` is off, so the scheduler cannot add a duplicate.
- **Capacity planning is off only while history is seeded.** Backdated job cards carry real time logs,
  and v16 counts other draft job cards' *scheduled* times as overlaps. The seed turns capacity planning
  off while it builds history and stories 1–2, then restores it. The not-started sofa work order is
  scheduled normally.
- **Job card time logs** fall inside 08:00–17:00 and never overlap per workstation, so the job cards read
  like a real shop floor.
- **Timber over-issue.** History work orders issue 1–6% more timber than the BOM, which differs from the
  BOM as SPEC asks. `transfer_extra_materials_percentage` is set to 15 to allow it.
- **VAT.** A "VAT 16%" Sales Taxes and Charges Template (display only) is applied to quotations, sales
  orders and invoices. Grand totals therefore include VAT. Margins are computed on net amounts.
- **Bespoke quotation validity.** ERPNext refuses to create a sales order from an expired quotation, so
  the bespoke quotation's validity runs 30 days from its date.
- **Mode of payment.** "Bank Transfer" is created with a sample bank account,
  *Business Current Account (Demo)*.
- **Demo user email.** It is `demo@<site>`. If the site name has no dot (as for local sites like
  `tira-studio`), `.localhost` is appended so the address is valid.
- **Fresh sites.** If the setup wizard has not run, the seed completes it non-interactively: Kenya,
  KES, Africa/Nairobi, Standard chart, and a calendar-year fiscal year that the seed extends
  backwards as needed. No wizard user is created.
- **Existing company.** If the company already exists (for example from the setup wizard), the seed uses
  it and its existing abbreviation instead of the `abbr` argument.
- **Missing ERPNext contact fields.** Some v16 sites lack ERPNext's own Address/Contact custom fields
  (`Contact.is_billing_contact`), and invoicing fails without them. If they are missing, the seed calls
  ERPNext's `create_address_and_contact_custom_fields()`.
- **Banner position.** The "Demo system by ERP Kenya" banner is a slim fixed bar at the bottom of the
  desk. It never overlaps the v16 navbar and is hidden in print.
- **Walkthrough step 4 uses Stock Projected Qty, not Stock Balance.** Stock Balance is a background
  (prepared) report in v16, so the prospect would land on "generate a new report". Stock Projected Qty
  runs instantly and shows actual, reserved and projected qty per warehouse, including the fabric
  shortage.
- **Valuation reposts are run by the seed.** Backdated stock entries queue ERPNext Repost Item
  Valuation jobs. Demo sites keep the scheduler off, so the seed processes them at the end of each
  stock phase. Otherwise reports would keep warning "reposting in progress". For existing sites:
  `bench execute erpk_demo.tools.process_reposts`.
- **User list.** Frappe lets any desk user list all non-standard users. This app adds a User
  permission query (`erpk_demo/permissions.py`): users without System Manager see only their own User
  record. The User list still opens for the demo user (it is their own profile), but it lists nobody
  else.
- **Workspace widgets.** v16 workspace blocks find number cards and charts by their row label. Custom
  number cards also need a readable `document_type` (Bin / Stock Entry), and no currency, to show
  for non-admins.
- **ERPK print formats draw their own header** (company name or logo, title, draft badge) and skip the
  standard letter head and print heading. The plain company letter head is created in the masters
  phase, so standard formats use it too.

## Layout

- Tests live in `erpk_demo/tests/` (inside the Python package) rather than a root `tests/` folder,
  because `bench run-tests` only discovers tests inside the package.
- `erpk_demo/setup/fixture_records.py` builds the fixture records, which are then exported to
  `erpk_demo/fixtures/`. The fixtures stay readable and can be regenerated.
- The fixture list in `hooks.py` matches SPEC §6.
- Extra scripts: `bin/make_golden.sh` (golden backup) and `bin/_guard.sh` (the shared "site must contain
  demo" guard).
