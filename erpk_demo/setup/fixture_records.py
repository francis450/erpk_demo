"""Builds the records this app ships as fixtures. Developer tool, not part of the seed.

    bench --site <dev site> execute erpk_demo.setup.fixture_records.build
    bench --site <dev site> export-fixtures --app erpk_demo

Fresh sites get these from `erpk_demo/fixtures/*.json` on install/migrate. Nothing here is
prospect specific: it reads no profile and names no company.
"""

import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

MODULE = "ERPK Demo"
WORKSPACE = "Workshop"
START_HERE_BLOCK = "ERPK Start Here"
CHART = "ERPK Wood Utilisation by Month"
CHART_LABEL = "Wood utilisation by month"
# Workspace content blocks find their widget by the row label, not the record name.

DEMO_ROLES = [
	"Sales User",
	"Sales Manager",
	"Stock User",
	"Stock Manager",
	"Manufacturing User",
	"Manufacturing Manager",
	"Purchase User",
	"Accounts User",
]

# Navigation-only: hides modules from the demo user's desk (DocPerm still governs access).
HIDDEN_MODULES = [
	"CRM",
	"Projects",
	"Support",
	"Quality Management",
	"Website",
	"Assets",
	"Maintenance",
	"Telephony",
	"EDI",
	"Bulk Transaction",
	"Subcontracting",
	"ERPNext Integrations",
	"Integrations",
	"Payment Gateways",
	"Payments",
	"Portal",
	"Utilities",
	"Automation",
	"Build",
	"Data",
	"Workflow",
	"Email",
	"Users",
	"System",
	# not installed on a standard v16 bench, listed so a site that has them hides them too
	"HR",
	"Payroll",
	"Loan Management",
]

NUMBER_CARDS = [
	{
		"name": "ERPK Open Work Orders",
		"label": "Open Work Orders",
		"type": "Document Type",
		"document_type": "Work Order",
		"function": "Count",
		"filters_json": json.dumps(
			[["Work Order", "docstatus", "=", 1], ["Work Order", "status", "in", ["Not Started", "In Process"]]]
		),
		"color": "#006EFB",
	},
	{
		"name": "ERPK Raw Materials Below Reorder",
		"label": "Raw materials below reorder level",
		"type": "Custom",
		"method": "erpk_demo.api.below_reorder_count",
		# v16 shows a Custom card only to users who can read its document_type
		"document_type": "Bin",
		"color": "#E24C4C",
	},
	{
		"name": "ERPK Wood Utilisation This Month",
		"label": "Wood utilisation this month (%)",
		"type": "Custom",
		"method": "erpk_demo.api.utilisation_this_month",
		"document_type": "Stock Entry",
		"color": "#109A67",
	},
	{
		"name": "ERPK Sales Orders To Deliver",
		"label": "Sales Orders to deliver",
		"type": "Document Type",
		"document_type": "Sales Order",
		"function": "Count",
		"filters_json": json.dumps(
			[
				["Sales Order", "docstatus", "=", 1],
				["Sales Order", "status", "in", ["To Deliver and Bill", "To Deliver"]],
			]
		),
		"color": "#152D5D",
	},
]

SHORTCUTS = [
	("Quotation", "DocType", "List"),
	("Sales Order", "DocType", "List"),
	("Work Order", "DocType", "List"),
	("BOM", "DocType", "List"),
	("Stock Entry", "DocType", "List"),
	("Stock Balance", "Report", ""),
]

START_HERE_HTML = """<div class="erpk-start">
	<div class="erpk-start-head">
		<span class="erpk-start-kicker">Start here</span>
		<span class="erpk-start-sub">Six short steps through the demo. Follow them in order.</span>
	</div>
	<ol class="erpk-start-list"><li class="erpk-start-loading">Loading…</li></ol>
</div>"""

START_HERE_CSS = """.erpk-start { border: 1px solid var(--border-color); border-left: 4px solid #006EFB;
	border-radius: var(--border-radius-md); padding: 14px 18px; background: var(--card-bg); }
.erpk-start-head { display: flex; flex-wrap: wrap; align-items: baseline; gap: 10px; margin-bottom: 8px; }
.erpk-start-kicker { font-weight: 700; color: #152D5D; font-size: var(--text-lg); }
.erpk-start-sub { color: var(--text-muted); font-size: var(--text-sm); }
.erpk-start-list { margin: 0; padding-left: 0; list-style: none; counter-reset: step;
	display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 6px 18px; }
.erpk-start-list li { counter-increment: step; display: flex; align-items: center; gap: 10px; padding: 6px 0; }
.erpk-start-list li::before { content: counter(step); flex: none; width: 24px; height: 24px; border-radius: 50%;
	background: #152D5D; color: #fff; font-size: 12px; font-weight: 700; display: grid; place-items: center; }
.erpk-start-list li.erpk-start-loading::before { display: none; }
.erpk-start-list a { color: var(--text-color); font-weight: 500; }
.erpk-start-list a:hover { color: #006EFB; text-decoration: underline; }"""

START_HERE_JS = """frappe.xcall("erpk_demo.api.start_here").then((links) => {
	const list = root_element.querySelector(".erpk-start-list");
	if (!links || !links.length) {
		list.innerHTML = "<li class='erpk-start-loading'>Run the demo seed to fill these links.</li>";
		return;
	}
	list.innerHTML = "";
	links.forEach((link) => {
		const li = document.createElement("li");
		const a = document.createElement("a");
		a.textContent = link.label;
		a.href = link.route;
		a.addEventListener("click", (e) => {
			e.preventDefault();
			frappe.route_options = link.options || null;
			frappe.set_route(link.route.replace(/^\\/(app|desk)\\//, ""));
		});
		li.appendChild(a);
		list.appendChild(li);
	});
});"""


def build():
	custom_fields()
	start_here_block()
	number_cards()
	chart()
	workspace()
	print_formats()
	profiles()
	frappe.db.commit()
	print("fixture records built; now run: bench --site <site> export-fixtures --app erpk_demo")


def custom_fields():
	row = [
		{
			"fieldname": "erpk_unit_cost",
			"label": "Est. Unit Cost",
			"fieldtype": "Currency",
			"options": "currency",
			"insert_after": "net_amount",
			"read_only": 1,
			"print_hide": 1,
			"in_list_view": 1,
			"columns": 1,
		},
		{
			"fieldname": "erpk_margin_pct",
			"label": "Est. Margin %",
			"fieldtype": "Percent",
			"precision": "1",
			"insert_after": "erpk_unit_cost",
			"read_only": 1,
			"print_hide": 1,
			"in_list_view": 1,
			"columns": 1,
		},
	]
	create_custom_fields(
		{
			"Quotation Item": row,
			"Sales Order Item": [{**f, "in_list_view": 0} for f in row],
			"Quotation": [
				{
					"fieldname": "erpk_costing_section",
					"label": "Costing (internal)",
					"fieldtype": "Section Break",
					"insert_after": "in_words",
					"print_hide": 1,
					"collapsible": 0,
				},
				{
					"fieldname": "erpk_total_cost",
					"label": "Est. Total Cost",
					"fieldtype": "Currency",
					"options": "currency",
					"insert_after": "erpk_costing_section",
					"read_only": 1,
					"print_hide": 1,
				},
				{
					"fieldname": "erpk_costing_cb",
					"fieldtype": "Column Break",
					"insert_after": "erpk_total_cost",
					"print_hide": 1,
				},
				{
					"fieldname": "erpk_margin_pct",
					"label": "Est. Margin %",
					"fieldtype": "Percent",
					"precision": "1",
					"insert_after": "erpk_costing_cb",
					"read_only": 1,
					"print_hide": 1,
				},
			],
		},
		update=True,
	)


def upsert(doctype, name, values):
	if frappe.db.exists(doctype, name):
		doc = frappe.get_doc(doctype, name)
		doc.update(values)
		doc.save(ignore_permissions=True)
	else:
		doc = frappe.get_doc({"doctype": doctype, "name": name, **values})
		doc.flags.name_set = True
		doc.insert(ignore_permissions=True, set_name=name)
	return doc


def start_here_block():
	upsert(
		"Custom HTML Block",
		START_HERE_BLOCK,
		{"html": START_HERE_HTML, "style": START_HERE_CSS, "script": START_HERE_JS, "private": 0},
	)


def number_cards():
	for card in NUMBER_CARDS:
		values = {k: v for k, v in card.items() if k != "name"}
		# no currency: the widget would format counts and percentages as money
		upsert(
			"Number Card",
			card["name"],
			{**values, "module": MODULE, "is_public": 1, "is_standard": 0, "currency": None},
		)


def chart():
	upsert(
		"Dashboard Chart",
		CHART,
		{
			"chart_name": CHART,
			"chart_type": "Report",
			"report_name": "Wood Utilisation",
			"use_report_chart": 1,
			"type": "Line",
			"timeseries": 0,
			"is_public": 1,
			"is_standard": 0,
			"module": MODULE,
			"filters_json": json.dumps({"group_by": "Month"}),
			"dynamic_filters_json": json.dumps(
				{
					"company": 'frappe.defaults.get_user_default("Company")',
					"from_date": "frappe.datetime.add_months(frappe.datetime.get_today(), -5).slice(0, 8) + '01'",
					"to_date": "frappe.datetime.get_today()",
				}
			),
			"color": "#109A67",
		},
	)


def workspace():
	blocks = [
		{"id": "erpkstart0", "type": "custom_block", "data": {"custom_block_name": START_HERE_BLOCK, "col": 12}},
		{"id": "erpkspace1", "type": "spacer", "data": {"col": 12}},
	]
	blocks += [
		{"id": f"erpkcard{i}0", "type": "number_card", "data": {"number_card_name": c["label"], "col": 3}}
		for i, c in enumerate(NUMBER_CARDS)
	]
	blocks += [
		{"id": "erpkchart0", "type": "chart", "data": {"chart_name": CHART_LABEL, "col": 12}},
		{"id": "erpkhead01", "type": "header", "data": {"text": '<span class="h4"><b>Shortcuts</b></span>', "col": 12}},
	]
	blocks += [
		{"id": f"erpkshort{i}", "type": "shortcut", "data": {"shortcut_name": label, "col": 4}}
		for i, (label, _t, _v) in enumerate(SHORTCUTS)
	]

	values = {
		"label": WORKSPACE,
		"title": WORKSPACE,
		"module": MODULE,
		"public": 1,
		"is_hidden": 0,
		"icon": "tool",
		"sequence_id": 0.5,
		"content": json.dumps(blocks),
		"custom_blocks": [{"custom_block_name": START_HERE_BLOCK, "label": START_HERE_BLOCK}],
		"number_cards": [{"number_card_name": c["name"], "label": c["label"]} for c in NUMBER_CARDS],
		"charts": [{"chart_name": CHART, "label": CHART_LABEL}],
		"shortcuts": [
			{"label": label, "link_to": label, "type": typ, "doc_view": view, "color": "Blue"}
			for label, typ, view in SHORTCUTS
		],
	}
	if frappe.db.exists("Workspace", WORKSPACE):
		doc = frappe.get_doc("Workspace", WORKSPACE)
		for table in ("custom_blocks", "number_cards", "charts", "shortcuts"):
			doc.set(table, [])
		doc.update(values)
		doc.save(ignore_permissions=True)
	else:
		from frappe.desk.doctype.workspace.workspace import add_to_sidebar

		doc = frappe.get_doc({"doctype": "Workspace", **values})
		doc.insert(ignore_permissions=True)
		add_to_sidebar(doc)


def print_formats():
	for name, doctype, title in (
		("ERPK Quotation", "Quotation", "Quotation"),
		("ERPK Sales Invoice", "Sales Invoice", "Invoice"),
	):
		upsert(
			"Print Format",
			name,
			{
				"doc_type": doctype,
				"module": MODULE,
				"standard": "No",
				"custom_format": 1,
				"print_format_type": "Jinja",
				"disabled": 0,
				"html": f'{{% set erpk_title = "{title}" %}}\n'
				'{% include "erpk_demo/templates/print/erpk_document.html" %}',
			},
		)


def profiles():
	upsert(
		"Role Profile",
		"ERPK Demo User",
		{"role_profile": "ERPK Demo User", "roles": [{"role": r} for r in DEMO_ROLES]},
	)
	modules = set(frappe.get_all("Module Def", pluck="name"))
	upsert(
		"Module Profile",
		"ERPK Demo Modules",
		{
			"module_profile_name": "ERPK Demo Modules",
			"block_modules": [{"module": m} for m in HIDDEN_MODULES if m in modules],
		},
	)
