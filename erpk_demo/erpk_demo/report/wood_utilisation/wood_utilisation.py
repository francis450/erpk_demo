"""Wood Utilisation: progress against the waste-free workshop goal.

utilisation % = (timber issued − timber offcuts returned) / timber issued × 100

Timber issued: raw material rows from items in the timber group, on submitted Manufacture
stock entries. Offcuts: scrap rows on the same entries whose stock UOM is the timber UOM.
Sawdust (scrap in Kg) is reported alongside but is not part of the percentage.
"""

from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import flt, get_first_day, getdate

DEFINITION = _(
	"Utilisation % = (timber issued − timber offcuts returned) ÷ timber issued × 100, "
	"from Manufacture entries. Timber is every item in the {0} group; offcuts are scrap returned "
	"in {1}. Sawdust is shown in kg but not counted in the percentage."
)


def target():
	return flt(frappe.conf.get("erpk_utilisation_target", 80))


def timber_group():
	return frappe.conf.get("erpk_timber_group", "Timber")


def execute(filters=None):
	filters = frappe._dict(filters or {})
	rows = manufacture_rows(filters.company, filters.from_date, filters.to_date, filters.work_order)
	group_by = filters.group_by or "Month"

	data = summarise(rows, group_by)
	months = summarise(rows, "Month")
	uom = timber_uom()
	message = f"<p class='text-muted'>{DEFINITION.format(timber_group(), uom)}</p>"
	return columns(group_by, uom), data, message, chart(months)


def utilisation_by_month(company, from_date, to_date, work_order=None):
	"""Used by the seed checks and the workspace number card."""
	return summarise(manufacture_rows(company, from_date, to_date, work_order), "Month")


def timber_uom():
	uoms = frappe.get_all("Item", filters={"item_group": timber_group()}, pluck="stock_uom", distinct=True)
	return uoms[0] if uoms else "Board Foot"


def manufacture_rows(company, from_date, to_date, work_order=None):
	se = frappe.qb.DocType("Stock Entry")
	sed = frappe.qb.DocType("Stock Entry Detail")
	item = frappe.qb.DocType("Item")
	query = (
		frappe.qb.from_(sed)
		.join(se)
		.on(sed.parent == se.name)
		.join(item)
		.on(item.name == sed.item_code)
		.select(
			se.name.as_("stock_entry"),
			se.posting_date,
			se.work_order,
			sed.item_code,
			sed.s_warehouse,
			sed.t_warehouse,
			sed.is_finished_item,
			sed.secondary_item_type,
			sed.transfer_qty,
			sed.stock_uom,
			item.item_group,
		)
		.where((se.docstatus == 1) & (se.purpose == "Manufacture"))
		.orderby(se.posting_date)
	)
	if company:
		query = query.where(se.company == company)
	if from_date:
		query = query.where(se.posting_date >= from_date)
	if to_date:
		query = query.where(se.posting_date <= to_date)
	if work_order:
		query = query.where(se.work_order == work_order)
	return query.run(as_dict=True)


def summarise(rows, group_by):
	group = timber_group()
	uom = timber_uom()
	buckets = defaultdict(lambda: {"issued": 0.0, "offcuts": 0.0, "sawdust": 0.0, "produced": set()})
	period_start = {}

	for r in rows:
		if group_by == "Work Order":
			key = r.work_order or r.stock_entry
		else:
			key = get_first_day(r.posting_date).strftime("%Y-%m")
		period_start.setdefault(key, get_first_day(r.posting_date))
		b = buckets[key]
		if r.s_warehouse and r.item_group == group:
			b["issued"] += flt(r.transfer_qty)
		elif r.t_warehouse and r.secondary_item_type == "Scrap":
			if r.stock_uom == uom:
				b["offcuts"] += flt(r.transfer_qty)
			elif r.stock_uom == "Kg":
				b["sawdust"] += flt(r.transfer_qty)
		elif r.t_warehouse and r.is_finished_item:
			b["produced"].add(r.item_code)

	goal = target()
	out = []
	for key, b in buckets.items():
		if not b["issued"]:
			continue
		utilisation = (b["issued"] - b["offcuts"]) / b["issued"] * 100
		out.append(
			{
				"period": key,
				"period_start": period_start[key],
				"work_order": key if group_by == "Work Order" else None,
				"item_produced": ", ".join(sorted(b["produced"])),
				"timber_issued": b["issued"],
				"offcuts": b["offcuts"],
				"utilisation": utilisation,
				"sawdust": b["sawdust"],
				"target": goal,
				"variance": utilisation - goal,
			}
		)
	return sorted(out, key=lambda d: (getdate(d["period_start"]), d["period"]))


def columns(group_by, uom):
	first = (
		{"label": _("Work Order"), "fieldname": "work_order", "fieldtype": "Link", "options": "Work Order", "width": 170}
		if group_by == "Work Order"
		else {"label": _("Month"), "fieldname": "period", "fieldtype": "Data", "width": 100}
	)
	return [
		first,
		{"label": _("Item Produced"), "fieldname": "item_produced", "fieldtype": "Data", "width": 200},
		{"label": _("Timber Issued ({0})").format(uom), "fieldname": "timber_issued", "fieldtype": "Float", "width": 150},
		{"label": _("Offcuts ({0})").format(uom), "fieldname": "offcuts", "fieldtype": "Float", "width": 130},
		{"label": _("Utilisation %"), "fieldname": "utilisation", "fieldtype": "Percent", "width": 120},
		{"label": _("Sawdust (kg)"), "fieldname": "sawdust", "fieldtype": "Float", "width": 110},
		{"label": _("Target %"), "fieldname": "target", "fieldtype": "Percent", "width": 90},
		{"label": _("Variance"), "fieldname": "variance", "fieldtype": "Float", "precision": 1, "width": 90},
	]


def chart(months):
	if not months:
		return None
	labels = [getdate(m["period_start"]).strftime("%b %Y") for m in months]
	return {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": _("Utilisation %"), "values": [round(m["utilisation"], 1) for m in months]},
				{"name": _("Target %"), "values": [target()] * len(months)},
			],
		},
		"type": "line",
		"colors": ["#109A67", "#152D5D"],
		"fieldtype": "Percent",
		"lineOptions": {"dotSize": 5, "regionFill": 0},
		"axisOptions": {"xIsSeries": 1},
	}
