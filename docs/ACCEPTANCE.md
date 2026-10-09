# ACCEPTANCE — definition of done

Run all checks on a **fresh** local v16 site (create a throwaway site
`erpk-test.demo.localhost` for this; ask before dropping any site).

## A. Install and seed
- [ ] `bench new-site … --install-app erpnext --install-app erpk_demo` succeeds with no errors.
- [ ] `seed.run` completes; summary log shows counts matching SEED_DATA §13.
- [ ] Running `seed.run` a second time completes with zero new records and no errors.
- [ ] Seeding with a different `company`/`abbr` on another fresh site works
      (proves nothing is hard-coded).
- [ ] `grep -ri tira erpk_demo/` returns hits only in `seed/profiles/` and docs.

## B. The six walkthrough links (log in as the demo user, not Administrator)
1. [ ] DT-6S BOM opens; shows materials, operations, scrap, and a total cost;
       margin at Standard Selling is 45–70%.
2. [ ] Draft quotation opens; every row shows Est. Unit Cost and Est. Margin %;
       changing a rate recomputes margins live; colours: DT-6S green, TV-180 orange.
3. [ ] Bespoke sales order shows Delivered + Billed 100%; links reach Work Order,
       Job Cards, Manufacture entry, Delivery Note, Sales Invoice, Payment Entries.
4. [ ] Stock Balance shows stock in Raw Materials, Finished Goods/showrooms, and
       Scrap; Ngong Road and Redhill each hold at least two finished pieces.
5. [ ] Material Request for UPH-LIN-OAT exists; Stock Projected Qty shows fabric
       short against the sofa Work Order.
6. [ ] Wood Utilisation report: ≥5 months, chart with target line, trend rises
       from ~72% to ≥80% in the last full month, current month just under 80%.

## C. Demo user safety
- [ ] Demo user cannot open System Settings, User list, Role, Custom Field,
      Customize Form, or Data Import.
- [ ] Demo user lands on the Workshop workspace after login.
- [ ] Hidden modules (HR, Payroll, CRM, etc.) are not visible in the sidebar.
- [ ] Persistent "Demo system by ERP Kenya" banner is visible on every page.

## D. Production readiness
- [ ] `mute_emails` is 1; submitting a Sales Invoice with an email-able customer
      sends nothing (check Email Queue is empty or all marked not sent).
- [ ] `bin/reset_demo.sh` refuses a site name without `demo`; with a valid site and
      `--yes`, restores golden state (a test quotation created before reset is gone
      after).
- [ ] `/robots.txt` disallows all; sign-up page is disabled.
- [ ] Print preview of Quotation (ERPK Quotation) shows brand colours and ERP Kenya
      footer and **no** cost/margin fields.
- [ ] No mention of KRA, eTIMS or M-Pesa anywhere in the app or seed (`grep -ri`).

## E. Tests
- [ ] `bench --site <test site> run-tests --app erpk_demo` passes. Minimum tests:
      seed idempotency; `get_item_unit_cost` returns BOM unit cost; Wood
      Utilisation calculation on a known manufacture entry; reset script guard.

## F. Hand-off
- [ ] `README.md` and `docs/DEVIATIONS.md` written.
- [ ] Screenshots of the six walkthrough steps saved to `docs/screenshots/`.
- [ ] Short report to the user: what was built, deviations, anything needing a decision.
