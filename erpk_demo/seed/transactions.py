"""Phases 2-4: opening stock, backdated history, demo stories.

Every document is recorded in a per-site registry (DefaultValue, parent `__erpk_demo`)
under a stable key, so re-running skips what already exists. Stock postings are made in
date order so no backdated reposts are needed.
"""

import datetime
from contextlib import contextmanager

import frappe
from frappe.utils import add_days, add_months, flt, get_datetime, get_first_day, get_last_day, getdate, today

from erpk_demo.seed import masters
from erpk_demo.seed.masters import bank_account, customer, default_bom, supplier, vat_template

REGISTRY = "__erpk_demo"
WORKDAY = (8, 17)  # job card time logs fall inside 08:00-17:00


@contextmanager
def capacity_planning_off():
	"""Backdated job cards carry real time logs; ERPNext's forward scheduling of other open cards
	would otherwise collide with them. Restored afterwards."""
	before = frappe.db.get_single_value("Manufacturing Settings", "disable_capacity_planning")
	frappe.db.set_single_value("Manufacturing Settings", "disable_capacity_planning", 1)
	try:
		yield
	finally:
		frappe.db.set_single_value("Manufacturing Settings", "disable_capacity_planning", before)


# ── Registry ────────────────────────────────────────────────────────────────


def registered(ctx, key, doctype):
	name = frappe.db.get_default(f"{ctx.abbr}:{key}", parent=REGISTRY)
	if name and frappe.db.exists(doctype, {"name": name, "docstatus": ["<", 2]}):
		return name


def keyed(ctx, key, doctype, create):
	"""Return the registered doc for `key`, or build it with `create()` and register it."""
	if name := registered(ctx, key, doctype):
		ctx.count(doctype, False)
		return frappe.get_doc(doctype, name)
	doc = create()
	frappe.db.set_default(f"{ctx.abbr}:{key}", doc.name, parent=REGISTRY)
	ctx.count(doctype, True)
	return doc


def lookup(ctx, key, doctype):
	"""Registered doc name for other modules (workspace links, checks)."""
	return registered(ctx, key, doctype)


# ── Dates ───────────────────────────────────────────────────────────────────


def month_day(offset, day):
	start = get_first_day(add_months(today(), offset))
	return min(add_days(start, day - 1), get_last_day(start))


def at(date, hour=9, minute=0):
	return datetime.datetime.combine(getdate(date), datetime.time(hour, minute))


def set_posting(doc, dt):
	dt = get_datetime(dt)
	doc.set_posting_time = 1
	doc.posting_date = dt.date()
	doc.posting_time = dt.time().strftime("%H:%M:%S")


class Floor:
	"""Per-workstation clock so job card time logs never overlap and stay in working hours."""

	def __init__(self):
		self.free = {}

	@staticmethod
	def chunks(start, minutes):
		t = get_datetime(start)
		while minutes > 0.01:
			if t.hour < WORKDAY[0]:
				t = t.replace(hour=WORKDAY[0], minute=0, second=0)
			end_of_day = t.replace(hour=WORKDAY[1], minute=0, second=0)
			if t >= end_of_day:
				t = (t + datetime.timedelta(days=1)).replace(hour=WORKDAY[0], minute=0, second=0)
				continue
			take = min(minutes, (end_of_day - t).total_seconds() / 60)
			yield t, t + datetime.timedelta(minutes=take)
			t += datetime.timedelta(minutes=take)
			minutes -= take

	def plan(self, operations, start):
		"""[(operation, workstation, minutes)] -> ([(operation, [(from, to)])], finish)"""
		t = get_datetime(start)
		plan = []
		for op, ws, minutes in operations:
			t = max(t, self.free.get(ws, t))
			logs = list(self.chunks(t, minutes))
			t = logs[-1][1]
			self.free[ws] = t
			plan.append((op, logs))
		return plan, t


# ── Phase: opening ──────────────────────────────────────────────────────────


def opening(ctx):
	p = ctx.profile
	posting = at(add_days(today(), -p.OPENING_DAYS_AGO), 8)
	temp_opening = ctx.acc("Temporary Opening")

	def recon(rows, dt):
		doc = frappe.get_doc(
			{
				"doctype": "Stock Reconciliation",
				"company": ctx.company,
				"purpose": "Opening Stock",
				"expense_account": temp_opening,
				"cost_center": ctx.cost_center(),
				"items": rows,
			}
		)
		set_posting(doc, dt)
		doc.insert(ignore_permissions=True)
		doc.submit()
		return doc

	keyed(
		ctx,
		"opening:raw",
		"Stock Reconciliation",
		lambda: recon(
			[
				{"item_code": code, "warehouse": ctx.wh("rm"), "qty": qty, "valuation_rate": rate}
				for code, _n, _g, _u, rate, qty, *_ in p.RAW_MATERIALS
			],
			posting,
		),
	)

	# BOM costs from the now-real valuation rates
	for item_code in p.BOMS:
		bom = frappe.get_doc("BOM", default_bom(item_code))
		bom.update_cost(update_parent=False, update_hour_rate=True, save=True)

	keyed(
		ctx,
		"opening:finished",
		"Stock Reconciliation",
		lambda: recon(
			[
				{
					"item_code": code,
					"warehouse": ctx.wh(wh),
					"qty": qty,
					"valuation_rate": unit_cost(code),
				}
				for code, wh, qty in p.OPENING_FINISHED
			],
			posting + datetime.timedelta(hours=1),
		),
	)


def unit_cost(item_code):
	bom = default_bom(item_code)
	total, qty = frappe.db.get_value("BOM", bom, ["total_cost", "quantity"])
	return flt(total) / flt(qty or 1)


# ── Manufacturing chain ─────────────────────────────────────────────────────


def bom_operations(bom_no):
	return [
		(r.operation, r.workstation, flt(r.time_in_mins))
		for r in frappe.get_all(
			"BOM Operation",
			filters={"parent": bom_no},
			fields=["operation", "workstation", "time_in_mins"],
			order_by="idx",
		)
	]


def make_work_order(ctx, item_code, qty, start, sales_order=None):
	bom_no = default_bom(item_code)
	wo = frappe.get_doc(
		{
			"doctype": "Work Order",
			"production_item": item_code,
			"bom_no": bom_no,
			"qty": qty,
			"company": ctx.company,
			"source_warehouse": ctx.wh("rm"),
			"wip_warehouse": ctx.wh("wip"),
			"fg_warehouse": ctx.wh("fg"),
			"scrap_warehouse": ctx.wh("scrap"),
			"planned_start_date": start,
		}
	)
	if sales_order:
		wo.sales_order = sales_order.name
		wo.sales_order_item = next(i.name for i in sales_order.items if i.item_code == item_code)
	wo.get_items_and_operations_from_bom()
	wo.insert(ignore_permissions=True)
	wo.submit()
	return wo


def timber_items(ctx):
	return set(frappe.get_all("Item", filters={"item_group": ctx.profile.TIMBER_GROUP}, pluck="name"))


def material_transfer(ctx, wo, dt, timber_factor):
	from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry

	se = frappe.get_doc(make_stock_entry(wo.name, "Material Transfer for Manufacture", wo.qty))
	timber = timber_items(ctx)
	for row in se.items:
		if row.item_code in timber:
			row.qty = flt(row.qty * timber_factor, 2)
	set_posting(se, dt)
	se.insert(ignore_permissions=True)
	se.submit()
	return se


def complete_job_cards(wo, plan, partial=None):
	"""Log time on each job card per `plan`. `partial`: {operation: fraction} leaves that card in progress;
	operations after a partial one stay open."""
	cards = {
		jc.operation: jc.name
		for jc in frappe.get_all("Job Card", filters={"work_order": wo.name, "docstatus": 0}, fields=["name", "operation"])
	}
	stop = False
	for op, logs in plan:
		if stop or op not in cards:
			continue
		jc = frappe.get_doc("Job Card", cards[op])
		jc.set("time_logs", [])
		if partial and op in partial:
			total = sum((t - f).total_seconds() for f, t in logs) * partial[op]
			for f, t in logs:
				if total <= 0:
					break
				t = min(t, f + datetime.timedelta(seconds=total))
				total -= (t - f).total_seconds()
				jc.append("time_logs", {"from_time": f, "to_time": t, "completed_qty": 0})
			jc.save(ignore_permissions=True)
			stop = True
			continue
		for i, (f, t) in enumerate(logs):
			jc.append(
				"time_logs",
				{"from_time": f, "to_time": t, "completed_qty": jc.for_quantity if i == len(logs) - 1 else 0},
			)
		jc.save(ignore_permissions=True)
		jc.submit()


def manufacture(ctx, wo, dt, timber_factor, utilisation):
	"""Manufacture entry with actual timber issued and offcuts giving `utilisation` %."""
	from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry

	p = ctx.profile
	se = frappe.get_doc(make_stock_entry(wo.name, "Manufacture", wo.qty))
	timber = timber_items(ctx)
	issued = 0
	for row in se.items:
		if row.s_warehouse and row.item_code in timber:
			row.qty = flt(row.qty * timber_factor, 2)
			issued += row.qty
	for row in se.items:
		if row.item_code == p.OFFCUT_ITEM and not row.s_warehouse:
			row.qty = flt(issued * (1 - utilisation / 100), 2)
		elif row.item_code == p.DUST_ITEM and not row.s_warehouse:
			row.qty = flt(row.qty * timber_factor, 2)
	set_posting(se, dt)
	se.insert(ignore_permissions=True)
	se.submit()
	return se


def move_stock(ctx, item_code, qty, from_key, to_key, dt):
	se = frappe.get_doc(
		{
			"doctype": "Stock Entry",
			"purpose": "Material Transfer",
			"stock_entry_type": "Material Transfer",
			"company": ctx.company,
			"from_warehouse": ctx.wh(from_key),
			"to_warehouse": ctx.wh(to_key),
			"items": [{"item_code": item_code, "qty": qty, "s_warehouse": ctx.wh(from_key), "t_warehouse": ctx.wh(to_key)}],
		}
	)
	set_posting(se, dt)
	se.insert(ignore_permissions=True)
	se.submit()
	return se


def build_chain(
	ctx, floor, key, item_code, qty, start, timber_factor, utilisation, dest=None, sales_order=None, not_before=None
):
	"""Steps (datetime, label, fn) for one work order from submit to showroom.
	`not_before` pushes the manufacture entry to at least that datetime."""
	wo_ref = {}
	bom_no = default_bom(item_code)
	transfer_at = get_datetime(start)
	plan, finish = floor.plan(
		[(op, ws, m * qty) for op, ws, m in bom_operations(bom_no)], transfer_at + datetime.timedelta(minutes=30)
	)
	made_at = finish + datetime.timedelta(minutes=15)
	if not_before:
		made_at = max(made_at, get_datetime(not_before))

	def wo():
		wo_ref["wo"] = keyed(
			ctx, f"{key}:wo", "Work Order", lambda: make_work_order(ctx, item_code, qty, transfer_at, sales_order)
		)
		return wo_ref["wo"]

	def transfer():
		keyed(ctx, f"{key}:transfer", "Stock Entry", lambda: material_transfer(ctx, wo_ref["wo"], transfer_at, timber_factor))

	def job_cards():
		if not registered(ctx, f"{key}:mfg", "Stock Entry"):
			complete_job_cards(frappe.get_doc("Work Order", wo_ref["wo"].name), plan)

	def mfg():
		keyed(
			ctx,
			f"{key}:mfg",
			"Stock Entry",
			lambda: manufacture(ctx, frappe.get_doc("Work Order", wo_ref["wo"].name), made_at, timber_factor, utilisation),
		)

	steps = [
		(transfer_at - datetime.timedelta(minutes=5), "wo", wo),
		(transfer_at, "transfer", transfer),
		(finish, "job cards", job_cards),
		(made_at, "manufacture", mfg),
	]
	if dest and dest != "fg":
		move_at = made_at + datetime.timedelta(minutes=30)
		steps.append(
			(move_at, "move", lambda: keyed(ctx, f"{key}:move", "Stock Entry", lambda: move_stock(ctx, item_code, qty, "fg", dest, move_at)))
		)
	return steps, made_at


# ── Selling / buying helpers ────────────────────────────────────────────────


def price(item_code, price_list):
	return flt(frappe.db.get_value("Item Price", {"item_code": item_code, "price_list": price_list}, "price_list_rate"))


def apply_vat(doc, ctx):
	from erpnext.controllers.accounts_controller import get_taxes_and_charges

	template = vat_template(ctx)
	doc.taxes_and_charges = template
	doc.set("taxes", get_taxes_and_charges("Sales Taxes and Charges Template", template))


def sales_invoice(ctx, cust_key, item_code, qty, wh_key, dt):
	si = frappe.get_doc(
		{
			"doctype": "Sales Invoice",
			"company": ctx.company,
			"customer": customer(ctx, cust_key),
			"update_stock": 1,
			"set_warehouse": ctx.wh(wh_key),
			"selling_price_list": "Standard Selling",
			"items": [{"item_code": item_code, "qty": qty, "rate": price(item_code, "Standard Selling"), "warehouse": ctx.wh(wh_key)}],
		}
	)
	set_posting(si, dt)
	si.due_date = si.posting_date
	apply_vat(si, ctx)
	si.insert(ignore_permissions=True)
	si.submit()
	return si


def receive_payment(ctx, dt, dn, dt_posting, amount=None, reference=None):
	from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

	pe = get_payment_entry(dt, dn, party_amount=amount, bank_account=bank_account(ctx))
	pe.mode_of_payment = ctx.profile.MODES_OF_PAYMENT[0]
	pe.posting_date = getdate(dt_posting)
	pe.reference_no = reference or f"TRF-{dn}"
	pe.reference_date = getdate(dt_posting)
	pe.insert(ignore_permissions=True)
	pe.submit()
	return pe


def purchase_invoice(ctx, sup_key, item_code, qty, dt):
	pi = frappe.get_doc(
		{
			"doctype": "Purchase Invoice",
			"company": ctx.company,
			"supplier": supplier(ctx, sup_key),
			"update_stock": 1,
			"set_warehouse": ctx.wh("rm"),
			"buying_price_list": "Standard Buying",
			"items": [{"item_code": item_code, "qty": qty, "rate": price(item_code, "Standard Buying"), "warehouse": ctx.wh("rm")}],
		}
	)
	set_posting(pi, dt)
	pi.due_date = pi.posting_date
	pi.bill_no = f"SUP-{getdate(dt).strftime('%y%m%d')}-{item_code}"
	pi.bill_date = pi.posting_date
	pi.insert(ignore_permissions=True)
	pi.submit()
	return pi


def run_steps(ctx, steps):
	for _dt, label, fn in sorted(steps, key=lambda s: s[0]):
		fn()


# ── Phase: history ──────────────────────────────────────────────────────────


def history(ctx):
	p = ctx.profile
	floor = Floor()
	steps = []
	jitter = p.UTILISATION_JITTER

	for offset in sorted(p.HISTORY):
		month = p.HISTORY[offset]
		for i, (sup_key, item_code, qty, day) in enumerate(month.get("purchases", [])):
			dt = at(month_day(offset, day), 10)
			key = f"h{offset}:buy{i}"
			steps.append((dt, "purchase", lambda k=key, s=sup_key, c=item_code, q=qty, d=dt: buy_and_pay(ctx, k, s, c, q, d)))

		for i, (item_code, day, dest) in enumerate(month["work_orders"]):
			chain, _ = build_chain(
				ctx,
				floor,
				f"h{offset}:wo{i}",
				item_code,
				1,
				at(month_day(offset, day), 8),
				month["timber_factor"],
				month["utilisation"] + jitter[i % len(jitter)],
				dest=dest,
			)
			steps += chain

		for i, (cust_key, item_code, qty, wh_key, day) in enumerate(month["sales"]):
			dt = at(month_day(offset, day), 15)
			paid = not (offset == max(p.HISTORY) and cust_key in p.UNPAID_HISTORY_CUSTOMERS)
			key = f"h{offset}:sale{i}"
			steps.append(
				(dt, "sale", lambda k=key, c=cust_key, it=item_code, q=qty, w=wh_key, d=dt, pd=paid: sell(ctx, k, c, it, q, w, d, pd))
			)

	with capacity_planning_off():
		run_steps(ctx, steps)
	ctx.floor = floor


def buy_and_pay(ctx, key, sup_key, item_code, qty, dt):
	pi = keyed(ctx, key, "Purchase Invoice", lambda: purchase_invoice(ctx, sup_key, item_code, qty, dt))
	keyed(ctx, f"{key}:pay", "Payment Entry", lambda: receive_payment(ctx, "Purchase Invoice", pi.name, dt))


def sell(ctx, key, cust_key, item_code, qty, wh_key, dt, paid):
	si = keyed(ctx, key, "Sales Invoice", lambda: sales_invoice(ctx, cust_key, item_code, qty, wh_key, dt))
	if paid:
		keyed(
			ctx,
			f"{key}:pay",
			"Payment Entry",
			lambda: receive_payment(ctx, "Sales Invoice", si.name, add_days(dt, 2)),
		)
	frappe.db.commit()


# ── Phase: stories ──────────────────────────────────────────────────────────


def stories(ctx):
	floor = getattr(ctx, "floor", None) or replay_floor(ctx)
	with capacity_planning_off():
		story_bespoke(ctx, floor)
		frappe.db.commit()
		story_in_progress(ctx, floor)
		frappe.db.commit()
	story_shortage(ctx)
	frappe.db.commit()
	story_open_quotation(ctx)


def replay_floor(ctx):
	"""Rebuild workstation clocks from the profile when stories run without history."""
	floor = Floor()
	for offset in sorted(ctx.profile.HISTORY):
		for item_code, day, _dest in ctx.profile.HISTORY[offset]["work_orders"]:
			floor.plan(bom_operations(default_bom(item_code)), at(month_day(offset, day), 8, 30))
	return floor


def current_month(days_ago):
	return max(getdate(add_days(today(), -days_ago)), get_first_day(today()))


def story_bespoke(ctx, floor):
	p = ctx.profile
	b = p.BESPOKE
	base = p.BOMS[b["base_item"]]
	group = p.BESPOKE_GROUP

	masters.ensure_item(ctx, b["item_code"], b["item_name"], group, "Nos", 0, default_wh=ctx.wh("fg"), is_purchase_item=0)
	masters.ensure_bom(ctx, b["item_code"], base, timber_factor=b["timber_factor"], hours_factor=b["hours_factor"])
	masters.ensure_item_price(ctx, b["item_code"], "Standard Selling", b["rate"])
	cust = customer(ctx, b["customer"])
	t = getdate(today())

	def quotation():
		q = frappe.get_doc(
			{
				"doctype": "Quotation",
				"company": ctx.company,
				"quotation_to": "Customer",
				"party_name": cust,
				"transaction_date": add_days(t, -25),
				"valid_till": add_days(t, 5),  # 30-day validity; ERPNext refuses orders from expired quotes
				"selling_price_list": "Standard Selling",
				"items": [{"item_code": b["item_code"], "qty": 1, "rate": b["rate"]}],
			}
		)
		apply_vat(q, ctx)
		q.insert(ignore_permissions=True)
		q.submit()
		return q

	q = keyed(ctx, "s1:quotation", "Quotation", quotation)

	def sales_order():
		from erpnext.selling.doctype.quotation.quotation import make_sales_order

		so = make_sales_order(q.name)
		so.transaction_date = add_days(t, -22)
		so.delivery_date = add_days(t, -3)
		for row in so.items:
			row.delivery_date = so.delivery_date
			row.warehouse = ctx.wh("fg")
		so.insert(ignore_permissions=True)
		so.submit()
		return so

	so = keyed(ctx, "s1:so", "Sales Order", sales_order)
	keyed(
		ctx,
		"s1:deposit",
		"Payment Entry",
		lambda: receive_payment(
			ctx, "Sales Order", so.name, add_days(t, -21), amount=flt(so.grand_total * b["deposit_pct"] / 100, 0), reference=f"DEP-{so.name}"
		),
	)

	# manufacture lands in the current month even if the job cards finished earlier
	made_on = current_month(5)
	chain, made_at = build_chain(
		ctx,
		floor,
		"s1:wo",
		b["item_code"],
		1,
		at(add_days(made_on, -6), 8),
		b["over_issue"],
		b["utilisation"],
		dest=b["deliver_from"],
		sales_order=so,
		not_before=at(made_on, 16),
	)
	run_steps(ctx, chain)

	deliver_at = max(at(add_days(t, -3), 11), made_at + datetime.timedelta(hours=2))
	deliver_at = min(deliver_at, at(t, 11))

	def delivery_note():
		from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note

		dn = make_delivery_note(so.name)
		dn.set_warehouse = ctx.wh(b["deliver_from"])
		for row in dn.items:
			row.warehouse = ctx.wh(b["deliver_from"])
		set_posting(dn, deliver_at)
		dn.insert(ignore_permissions=True)
		dn.submit()
		return dn

	dn = keyed(ctx, "s1:dn", "Delivery Note", delivery_note)

	def invoice():
		from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice

		si = make_sales_invoice(dn.name)
		set_posting(si, deliver_at + datetime.timedelta(minutes=30))
		si.due_date = si.posting_date
		si.allocate_advances_automatically = 1
		si.set_advances()
		si.insert(ignore_permissions=True)
		si.submit()
		return si

	si = keyed(ctx, "s1:si", "Sales Invoice", invoice)
	if flt(frappe.db.get_value("Sales Invoice", si.name, "outstanding_amount")) > 0:
		keyed(
			ctx,
			"s1:balance",
			"Payment Entry",
			lambda: receive_payment(ctx, "Sales Invoice", si.name, si.posting_date, reference=f"BAL-{si.name}"),
		)


def make_sales_order(ctx, cust_key, items, transaction_date, delivery_date):
	so = frappe.get_doc(
		{
			"doctype": "Sales Order",
			"company": ctx.company,
			"customer": customer(ctx, cust_key),
			"transaction_date": transaction_date,
			"delivery_date": delivery_date,
			"selling_price_list": "Standard Selling",
			"items": [
				{"item_code": code, "qty": qty, "rate": rate, "delivery_date": delivery_date, "warehouse": ctx.wh("fg")}
				for code, qty, rate in items
			],
		}
	)
	apply_vat(so, ctx)
	so.insert(ignore_permissions=True)
	so.submit()
	return so


def story_in_progress(ctx, floor):
	s = ctx.profile.IN_PROGRESS
	t = getdate(today())
	so = keyed(
		ctx,
		"s2:so",
		"Sales Order",
		lambda: make_sales_order(ctx, s["customer"], [(s["item_code"], 1, s["rate"])], add_days(t, -6), add_days(t, s["delivery_in_days"])),
	)
	start = at(add_days(t, -2), 8)
	wo = keyed(ctx, "s2:wo", "Work Order", lambda: make_work_order(ctx, s["item_code"], 1, start, so))
	keyed(ctx, "s2:transfer", "Stock Entry", lambda: material_transfer(ctx, wo, start, 1.0))

	if not registered(ctx, "s2:jobs", "Work Order"):
		ops = bom_operations(wo.bom_no)
		plan, _ = Floor().plan(ops, start + datetime.timedelta(minutes=30))
		first, second = ops[0][0], ops[1][0]
		# first operation done, second about half way, the rest still open
		joinery_done = min(0.5, _fraction_before_now(plan, second))
		complete_job_cards(wo, plan, partial={second: joinery_done})
		frappe.db.set_default(f"{ctx.abbr}:s2:jobs", wo.name, parent=REGISTRY)


def _fraction_before_now(plan, op):
	logs = dict(plan)[op]
	now = get_datetime()
	total = sum((t - f).total_seconds() for f, t in logs)
	done = sum((min(t, now) - f).total_seconds() for f, t in logs if f < now)
	return max(0.05, done / total if total else 0)


def story_shortage(ctx):
	s = ctx.profile.SHORTAGE
	t = getdate(today())
	rate = s["rate"]
	so = keyed(
		ctx,
		"s3:so",
		"Sales Order",
		lambda: make_sales_order(ctx, s["customer"], [(s["item_code"], s["qty"], rate)], add_days(t, -1), add_days(t, s["delivery_in_days"])),
	)
	keyed(ctx, "s3:wo", "Work Order", lambda: make_work_order(ctx, s["item_code"], s["qty"], at(add_days(t, 3), 8), so))
	keyed(ctx, "s3:mr", "Material Request", lambda: raise_reorder(ctx, s["material"]))


def raise_reorder(ctx, item_code):
	"""Draft purchase request from the item's reorder settings, sized like ERPNext's reorder job
	(max of reorder qty and the deficiency). Left in draft so Projected Qty still shows the gap."""
	from erpnext.stock.utils import get_bin

	reorder = frappe.get_all(
		"Item Reorder",
		filters={"parent": item_code},
		fields=["warehouse", "warehouse_reorder_level", "warehouse_reorder_qty"],
		limit=1,
	)[0]
	projected = flt(get_bin(item_code, reorder.warehouse).projected_qty)
	qty = max(flt(reorder.warehouse_reorder_qty), flt(reorder.warehouse_reorder_level) - projected)
	needed_by = add_days(today(), 3)
	mr = frappe.get_doc(
		{
			"doctype": "Material Request",
			"company": ctx.company,
			"material_request_type": "Purchase",
			"transaction_date": today(),
			"schedule_date": needed_by,
			"items": [{"item_code": item_code, "qty": qty, "warehouse": reorder.warehouse, "schedule_date": needed_by}],
		}
	)
	mr.insert(ignore_permissions=True)
	return mr


def story_open_quotation(ctx):
	s = ctx.profile.OPEN_QUOTATION

	def quotation():
		q = frappe.get_doc(
			{
				"doctype": "Quotation",
				"company": ctx.company,
				"quotation_to": "Customer",
				"party_name": customer(ctx, s["customer"]),
				"transaction_date": today(),
				"valid_till": add_days(today(), 30),
				"selling_price_list": "Standard Selling",
				"items": [{"item_code": code, "qty": qty, "rate": rate} for code, qty, rate in s["items"]],
			}
		)
		apply_vat(q, ctx)
		q.insert(ignore_permissions=True)
		return q

	q = keyed(ctx, "s4:quotation", "Quotation", quotation)
	from erpk_demo.api import fill_quotation_costs

	fill_quotation_costs(q)
