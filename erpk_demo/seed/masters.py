"""Phase 1: company setup and master data. Idempotent."""

import frappe
from frappe.utils import add_days, add_years, getdate, today

from erpk_demo.seed.common import ensure_doc


def run(ctx):
	p = ctx.profile
	ensure_company(ctx)
	ensure_fiscal_years(ctx, add_days(today(), -(p.OPENING_DAYS_AGO + 60)))
	configure_settings(ctx)
	ensure_vat_template(ctx)
	ensure_bank(ctx)

	for uom in p.UOMS:
		ensure_doc(ctx, "UOM", uom["uom_name"], uom)
	for group in p.ITEM_GROUPS:
		ensure_doc(ctx, "Item Group", group, {"item_group_name": group, "parent_item_group": "All Item Groups"})

	ensure_warehouses(ctx)
	ensure_parties(ctx)
	ensure_items(ctx)
	ensure_workstations(ctx)
	ensure_boms(ctx)


# ── Company & settings ──────────────────────────────────────────────────────


def ensure_company(ctx):
	if frappe.db.exists("Company", ctx.company):
		ctx.count("Company", False)
		existing_abbr = frappe.db.get_value("Company", ctx.company, "abbr")
		if existing_abbr != ctx.abbr:
			ctx.log(f"Company exists with abbr {existing_abbr}; using it instead of {ctx.abbr}")
			ctx.abbr = existing_abbr
	else:
		ensure_doc(
			ctx,
			"Company",
			ctx.company,
			{
				"company_name": ctx.company,
				"abbr": ctx.abbr,
				"country": "Kenya",
				"default_currency": "KES",
				"create_chart_of_accounts_based_on": "Standard Template",
				"chart_of_accounts": "Standard",
			},
		)

	if not frappe.db.get_value("Company", ctx.company, "default_operating_cost_account"):
		# workstation costs absorbed into stock value
		frappe.db.set_value(
			"Company", ctx.company, "default_operating_cost_account", ctx.acc("Expenses Included In Valuation")
		)

	frappe.db.set_single_value("Global Defaults", "default_company", ctx.company)
	frappe.db.set_default("company", ctx.company)
	if not frappe.db.get_value("Company", ctx.company, "enable_perpetual_inventory"):
		frappe.db.set_value("Company", ctx.company, "enable_perpetual_inventory", 1)


def ensure_fiscal_years(ctx, from_date):
	"""Make sure fiscal years cover from_date..today, extending backwards from the current one."""
	from erpnext.accounts.utils import get_fiscal_year

	from_date = getdate(from_date)
	current = get_fiscal_year(today(), company=ctx.company, as_dict=True)
	start = getdate(current.year_start_date)
	while start > from_date:
		end = add_days(start, -1)
		start = getdate(add_years(start, -1))
		name = f"{start.year}" if start.year == getdate(end).year else f"{start.year}-{getdate(end).year}"
		if not frappe.db.exists("Fiscal Year", {"year_start_date": start}):
			ensure_doc(
				ctx,
				"Fiscal Year",
				name,
				{"year": name, "year_start_date": start, "year_end_date": end},
			)
		else:
			ctx.count("Fiscal Year", False)


def configure_settings(ctx):
	if not frappe.get_meta("Contact").has_field("is_billing_contact"):
		# some v16 sites miss ERPNext's own Address/Contact fields; invoicing queries need them
		from erpnext.setup.install import create_address_and_contact_custom_fields

		create_address_and_contact_custom_fields()

	stock = frappe.get_single("Stock Settings")
	if stock.valuation_method != "Moving Average":
		if frappe.db.exists("Stock Ledger Entry", {"is_cancelled": 0}):
			ctx.log(f"Stock exists: leaving valuation method as {stock.valuation_method}")
		else:
			stock.valuation_method = "Moving Average"
	stock.allow_negative_stock = 0
	stock.auto_indent = 0  # the demo's shortage request is seeded as a draft; no scheduler duplicates
	stock.reorder_email_notify = 0
	stock.save()

	mfg = frappe.get_single("Manufacturing Settings")
	mfg.backflush_raw_materials_based_on = "BOM"
	mfg.allow_overtime = 1
	mfg.allow_production_on_holidays = 1
	mfg.disable_capacity_planning = 0
	# history pieces consume a little more timber than the BOM; allow that to be transferred
	mfg.transfer_extra_materials_percentage = 15
	mfg.save()

	selling = frappe.get_single("Selling Settings")
	selling.so_required = "No"
	selling.dn_required = "No"
	selling.save()


def ensure_vat_template(ctx):
	"""16% VAT shown on sales documents. Display only; no tax-authority integration."""
	vat_account = frappe.db.get_value(
		"Account", {"company": ctx.company, "account_type": "Tax", "account_name": ["like", "%VAT%"], "is_group": 0}
	)
	if not vat_account:
		parent = frappe.db.get_value(
			"Account", {"company": ctx.company, "account_name": "Duties and Taxes", "is_group": 1}
		)
		vat_account = ensure_doc(
			ctx,
			"Account",
			{"account_name": "VAT", "company": ctx.company},
			{"parent_account": parent, "account_type": "Tax", "tax_rate": 16},
		).name

	title = "VAT 16%"
	ensure_doc(
		ctx,
		"Sales Taxes and Charges Template",
		{"title": title, "company": ctx.company},
		{
			"taxes": [
				{
					"charge_type": "On Net Total",
					"account_head": vat_account,
					"description": "VAT @ 16%",
					"rate": 16,
					"cost_center": ctx.cost_center(),
				}
			],
		},
	)


def ensure_bank(ctx):
	p = ctx.profile
	parent = frappe.db.get_value("Account", {"company": ctx.company, "account_type": "Bank", "is_group": 1})
	account = ensure_doc(
		ctx,
		"Account",
		{"account_name": p.BANK_ACCOUNT, "company": ctx.company},
		{"parent_account": parent, "account_type": "Bank", "account_currency": "KES"},
	).name
	for mode in p.MODES_OF_PAYMENT:
		mop = ensure_doc(ctx, "Mode of Payment", mode, {"mode_of_payment": mode, "type": "Bank"})
		if not any(a.company == ctx.company for a in mop.accounts):
			mop.append("accounts", {"company": ctx.company, "default_account": account})
			mop.save()


def bank_account(ctx):
	return frappe.db.get_value("Account", {"account_name": ctx.profile.BANK_ACCOUNT, "company": ctx.company})


def vat_template(ctx):
	return frappe.db.get_value("Sales Taxes and Charges Template", {"title": "VAT 16%", "company": ctx.company})


# ── Stock structure ─────────────────────────────────────────────────────────


def ensure_warehouses(ctx):
	root = frappe.db.get_value("Warehouse", {"company": ctx.company, "is_group": 1, "parent_warehouse": ["is", "not set"]})
	for key, name in ctx.profile.WAREHOUSES.items():
		ensure_doc(
			ctx,
			"Warehouse",
			ctx.wh(key),
			{"warehouse_name": name, "company": ctx.company, "parent_warehouse": root},
		)

	# v16 keeps the manufacturing warehouse defaults on Company
	frappe.db.set_value(
		"Company",
		ctx.company,
		{
			"default_wip_warehouse": ctx.wh("wip"),
			"default_fg_warehouse": ctx.wh("fg"),
			"default_scrap_warehouse": ctx.wh("scrap"),
			"default_warehouse_for_sales_return": ctx.wh("fg"),
		},
	)
	frappe.db.set_single_value("Stock Settings", "default_warehouse", ctx.wh("rm"))


def ensure_parties(ctx):
	p = ctx.profile
	for c in p.CUSTOMERS.values():
		ensure_doc(
			ctx,
			"Customer",
			{"customer_name": c["customer_name"]},
			{**c, "territory": p.TERRITORY},
		)
	for s in p.SUPPLIERS.values():
		ensure_doc(ctx, "Supplier", {"supplier_name": s["supplier_name"]}, {**s, "country": "Kenya"})


def customer(ctx, key):
	return frappe.db.get_value("Customer", {"customer_name": ctx.profile.CUSTOMERS[key]["customer_name"]})


def supplier(ctx, key):
	return frappe.db.get_value("Supplier", {"supplier_name": ctx.profile.SUPPLIERS[key]["supplier_name"]})


def ensure_items(ctx):
	p = ctx.profile

	for code, name, group, uom, rate, _qty, level, reorder_qty, sup in p.RAW_MATERIALS:
		item = ensure_item(
			ctx,
			code,
			name,
			group,
			uom,
			rate,
			default_wh=ctx.wh("rm"),
			is_sales_item=0,
			default_supplier=supplier(ctx, sup),
		)
		if not item.reorder_levels:
			item.append(
				"reorder_levels",
				{
					"warehouse": ctx.wh("rm"),
					"warehouse_group": ctx.wh("rm"),
					"warehouse_reorder_level": level,
					"warehouse_reorder_qty": reorder_qty,
					"material_request_type": "Purchase",
				},
			)
			item.append("supplier_items", {"supplier": supplier(ctx, sup)})
			item.save()
		ensure_item_price(ctx, code, "Standard Buying", rate)

	for code, name, uom, rate in p.SCRAP_ITEMS:
		ensure_item(ctx, code, name, p.SCRAP_GROUP, uom, rate, default_wh=ctx.wh("scrap"), is_sales_item=0, is_purchase_item=0)

	for code, name, price in p.FINISHED_GOODS:
		ensure_item(ctx, code, name, p.FINISHED_GROUP, "Nos", 0, default_wh=ctx.wh("fg"), is_purchase_item=0)
		ensure_item_price(ctx, code, "Standard Selling", price)


def ensure_item(ctx, code, name, group, uom, rate, default_wh, is_sales_item=1, is_purchase_item=1, default_supplier=None):
	item = ensure_doc(
		ctx,
		"Item",
		code,
		{
			"item_code": code,
			"item_name": name,
			"description": name,
			"item_group": group,
			"stock_uom": uom,
			"is_stock_item": 1,
			"include_item_in_manufacturing": 1,
			"is_sales_item": is_sales_item,
			"is_purchase_item": is_purchase_item,
			"valuation_rate": rate,
			"item_defaults": [
				{"company": ctx.company, "default_warehouse": default_wh, "default_supplier": default_supplier}
			],
		},
	)
	if not any(d.company == ctx.company for d in item.item_defaults):
		item.append("item_defaults", {"company": ctx.company, "default_warehouse": default_wh, "default_supplier": default_supplier})
		item.save()
	return item


def ensure_item_price(ctx, item_code, price_list, rate):
	ensure_doc(
		ctx,
		"Item Price",
		{"item_code": item_code, "price_list": price_list},
		{"price_list_rate": rate},
	)


# ── Manufacturing ───────────────────────────────────────────────────────────


def ensure_workstations(ctx):
	p = ctx.profile
	for name, components in p.WORKSTATIONS.items():
		for component in components:
			ensure_doc(ctx, "Workstation Operating Component", component, {"component_name": component})
		ensure_doc(
			ctx,
			"Workstation",
			name,
			{
				"workstation_name": name,
				"workstation_costs": [
					{"operating_component": c, "operating_cost": cost} for c, cost in components.items()
				],
			},
		)
	for op, ws in p.OPERATIONS.items():
		ensure_doc(ctx, "Operation", op, {"name": op, "workstation": ws})


def default_bom(item_code):
	return frappe.db.get_value("BOM", {"item": item_code, "is_default": 1, "is_active": 1, "docstatus": 1})


def ensure_boms(ctx):
	for item_code, spec in ctx.profile.BOMS.items():
		ensure_bom(ctx, item_code, spec)


def ensure_bom(ctx, item_code, spec, timber_factor=1, hours_factor=1):
	"""Submitted default BOM with operations and scrap rows. Returns the BOM name."""
	if name := default_bom(item_code):
		ctx.count("BOM", False)
		return name

	timber = set(frappe.get_all("Item", filters={"item_group": ctx.profile.TIMBER_GROUP}, pluck="name"))
	offcut = ctx.profile.OFFCUT_ITEM
	bom = frappe.get_doc(
		{
			"doctype": "BOM",
			"item": item_code,
			"company": ctx.company,
			"quantity": 1,
			"is_active": 1,
			"is_default": 1,
			"with_operations": 1,
			"rm_cost_as_per": "Valuation Rate",
			"currency": "KES",
			"cost_allocation_per": 100,
			"items": [
				{"item_code": code, "qty": round(qty * (timber_factor if code in timber else 1), 2)}
				for code, qty in spec["items"].items()
			],
			"operations": [
				{
					"operation": op,
					"workstation": ctx.profile.OPERATIONS[op],
					"time_in_mins": round(hours * hours_factor * 60, 1),
				}
				for op, hours in spec["ops"].items()
			],
			"secondary_items": [
				{
					"item_code": code,
					"qty": round(qty * (timber_factor if code == offcut else 1), 2),
					"secondary_item_type": "Scrap",
					"valuation_type": "Valuation Rate",
				}
				for code, qty in spec["scrap"].items()
			],
		}
	)
	bom.insert(ignore_permissions=True)
	bom.submit()
	ctx.count("BOM", True)
	return bom.name
