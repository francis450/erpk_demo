"""SEED_DATA §13 final-state checks. Logged as warnings; never raise."""

import frappe
from frappe.utils import add_months, get_first_day, getdate, today


def final_checks(ctx):
	p = ctx.profile
	company = ctx.company
	raw_codes = {r[0] for r in p.RAW_MATERIALS}
	results = {}

	def check(label, ok, detail=""):
		results[label] = bool(ok)
		print(f"  [{'ok' if ok else 'WARN'}] {label} {detail}")

	print("\nerpk_demo final checks")
	items = lambda group: frappe.db.count("Item", {"item_group": group})  # noqa: E731
	check("finished items", items(p.FINISHED_GROUP) == len(p.FINISHED_GOODS), items(p.FINISHED_GROUP))
	check("bespoke items", items(p.BESPOKE_GROUP) >= 1, items(p.BESPOKE_GROUP))
	rm = frappe.db.count("Item", {"name": ["in", list(raw_codes)]})
	check("raw materials", rm == len(p.RAW_MATERIALS), rm)
	check("scrap items", items(p.SCRAP_GROUP) == len(p.SCRAP_ITEMS), items(p.SCRAP_GROUP))

	warehouses = [ctx.wh(k) for k in p.WAREHOUSES]
	stocked = frappe.get_all(
		"Bin", filters={"warehouse": ["in", warehouses], "actual_qty": [">", 0]}, pluck="warehouse", distinct=True
	)
	check("warehouses with stock", len(set(stocked)) >= 4, f"{len(set(stocked))}/{len(warehouses)}")

	wo = lambda status: frappe.db.count("Work Order", {"company": company, "status": status, "docstatus": 1})  # noqa: E731
	check("completed work orders", wo("Completed") >= 14, wo("Completed"))
	check("in-progress work order", wo("In Process") >= 1, wo("In Process"))
	check("not-started work order", wo("Not Started") >= 1, wo("Not Started"))

	mr = frappe.get_all(
		"Material Request Item",
		filters={"item_code": p.SHORTAGE["material"], "docstatus": ["<", 2]},
		pluck="parent",
	)
	check("shortage material request", len(mr) == 1, mr)

	q = frappe.get_all("Quotation", filters={"company": company, "docstatus": 0}, pluck="name")
	costed = all(
		all(r.erpk_unit_cost and r.erpk_margin_pct for r in frappe.get_doc("Quotation", n).items)
		for n in q
	) if q and frappe.get_meta("Quotation Item").has_field("erpk_unit_cost") else False
	check("draft quotation with costs", len(q) == 1 and costed, q)

	try:
		from erpk_demo.erpk_demo.report.wood_utilisation.wood_utilisation import utilisation_by_month

		months = utilisation_by_month(company, add_months(today(), -6), today())
		last_full = get_first_day(add_months(today(), -1))
		last = next((m for m in months if getdate(m["period_start"]) == last_full), None)
		check("utilisation months", len(months) >= 5, len(months))
		check("last full month >= target", last and last["utilisation"] >= 80, last and round(last["utilisation"], 1))
	except ImportError:
		check("utilisation report", False, "report not installed")

	return results
