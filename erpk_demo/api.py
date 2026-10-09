import frappe
from frappe.utils import flt


@frappe.whitelist()
def get_item_unit_cost(item_code: str, company: str | None = None) -> float:
	"""Default active BOM's total_cost / quantity; else the item's valuation rate; else 0."""
	if not item_code:
		return 0.0
	frappe.has_permission("Item", "read", throw=True)

	bom = frappe.db.get_value(
		"BOM",
		{"item": item_code, "is_default": 1, "is_active": 1, "docstatus": 1, **({"company": company} if company else {})},
		["total_cost", "quantity"],
		as_dict=True,
	)
	if bom and flt(bom.quantity):
		return flt(bom.total_cost) / flt(bom.quantity)

	return flt(
		frappe.db.get_value("Bin", {"item_code": item_code}, "valuation_rate", order_by="actual_qty desc")
		or frappe.db.get_value("Item", item_code, "valuation_rate")
	)


def margin_pct(net_amount, cost):
	net_amount = flt(net_amount)
	return (net_amount - flt(cost)) / net_amount * 100 if net_amount else 0.0


def fill_quotation_costs(doc):
	"""Server-side twin of public/js/quotation.js, used by the seed."""
	if not frappe.get_meta(doc.doctype).has_field("erpk_total_cost"):
		return
	total_cost = total_net = 0
	for row in doc.items:
		row.erpk_unit_cost = get_item_unit_cost(row.item_code, doc.company)
		row_cost = row.erpk_unit_cost * flt(row.qty)
		row.erpk_margin_pct = margin_pct(row.net_amount, row_cost)
		total_cost += row_cost
		total_net += flt(row.net_amount)
	doc.erpk_total_cost = total_cost
	doc.erpk_margin_pct = margin_pct(total_net, total_cost)
	if doc.docstatus == 0:
		doc.save(ignore_permissions=True)
	else:
		for row in doc.items:
			row.db_update()
		doc.db_update()
