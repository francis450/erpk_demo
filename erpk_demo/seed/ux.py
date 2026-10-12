"""Phase 5: site-specific UX on top of the fixtures: walkthrough links, branding, hardening,
demo user. Idempotent."""

import json

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter
from frappe.utils import add_months, get_first_day, today

from erpk_demo.seed.masters import default_bom
from erpk_demo.seed.transactions import REGISTRY, lookup

LOGO = "/assets/erpk_demo/images/erpkenya-logo.png"
WORKSPACE = "Workshop"
ROLE_PROFILE = "ERPK Demo User"
MODULE_PROFILE = "ERPK Demo Modules"


def run(ctx):
	start_here_links(ctx)
	letter_head(ctx)
	branding()
	print_defaults()
	harden()
	demo_user(ctx)
	cost_open_quotation(ctx)


def slug(doctype):
	return frappe.scrub(doctype).replace("_", "-")


def form(doctype, name):
	return f"/desk/{slug(doctype)}/{name}" if name else f"/desk/{slug(doctype)}"


def start_here_links(ctx):
	targets = {
		"open_quotation": lambda: form("Quotation", lookup(ctx, "s4:quotation", "Quotation")),
		"bespoke_sales_order": lambda: form("Sales Order", lookup(ctx, "s1:so", "Sales Order")),
		"shortage_material_request": lambda: form("Material Request", lookup(ctx, "s3:mr", "Material Request")),
		# Stock Balance is a background (prepared) report in v16; this one runs instantly and
		# shows actual, reserved and projected qty per warehouse
		"stock_balance": lambda: ("/desk/query-report/Stock Projected Qty", {"company": ctx.company}),
		"wood_utilisation": lambda: (
			"/desk/query-report/Wood Utilisation",
			{"company": ctx.company, "from_date": str(get_first_day(add_months(today(), -5))), "to_date": today()},
		),
	}
	links = []
	for label, key in ctx.profile.START_HERE:
		if key.startswith("bom:"):
			target = form("BOM", default_bom(key[4:]))
		else:
			target = targets[key]()
		route, options = target if isinstance(target, tuple) else (target, None)
		links.append({"label": label, "route": route, "options": options})
	frappe.db.set_default(f"start_here:{ctx.company}", json.dumps(links), parent=REGISTRY)


def letter_head(ctx):
	"""Plain letter head from the company name; no prospect logo."""
	name = ctx.company
	content = (
		'<div style="border-bottom:3px solid #152D5D;padding:4px 0 8px">'
		f'<div style="font-size:20px;font-weight:700;color:#152D5D">{frappe.utils.escape_html(ctx.company)}</div>'
		f'<div style="font-size:11px;color:#6b7280">{frappe.utils.escape_html(ctx.profile.DESCRIPTION)}</div>'
		"</div>"
	)
	values = {"letter_head_name": name, "source": "HTML", "content": content, "is_default": 1, "disabled": 0}
	if frappe.db.exists("Letter Head", name):
		doc = frappe.get_doc("Letter Head", name)
		doc.update(values)
		doc.save(ignore_permissions=True)
		ctx.count("Letter Head", False)
	else:
		frappe.get_doc({"doctype": "Letter Head", **values}).insert(ignore_permissions=True)
		ctx.count("Letter Head", True)
	frappe.db.set_value("Company", ctx.company, "default_letter_head", name)


def branding():
	frappe.db.set_single_value("Navbar Settings", "app_logo", LOGO)
	website = frappe.get_single("Website Settings")
	website.app_logo = LOGO
	website.app_name = "ERP Kenya Demo"
	website.save(ignore_permissions=True)


def print_defaults():
	for doctype, fmt in (("Quotation", "ERPK Quotation"), ("Sales Invoice", "ERPK Sales Invoice")):
		if frappe.db.exists("Print Format", fmt):
			make_property_setter(doctype, None, "default_print_format", fmt, "Data", for_doctype=True)


def harden():
	"""DEPLOY.md §4 settings that live in the database."""
	website = frappe.get_single("Website Settings")
	website.disable_signup = 1
	website.robots_txt = "User-agent: *\nDisallow: /"
	website.save(ignore_permissions=True)

	system = frappe.get_single("System Settings")
	system.session_expiry = "12:00"
	system.enable_password_policy = 1
	system.minimum_password_score = 2
	system.allow_consecutive_login_attempts = 5
	system.allow_login_after_fail = 300
	system.enable_two_factor_auth = 0
	system.save(ignore_permissions=True)


def demo_email():
	site = frappe.local.site
	return f"demo@{site if '.' in site else site + '.localhost'}"


def demo_user(ctx):
	email = demo_email()
	exists = frappe.db.exists("User", email)
	user = frappe.get_doc("User", email) if exists else frappe.new_doc("User")
	user.update(
		{
			"email": email,
			"first_name": "Demo",
			"last_name": "User",
			"user_type": "System User",
			"send_welcome_email": 0,
			"enabled": 1,
			"module_profile": MODULE_PROFILE,
			"default_workspace": WORKSPACE,
		}
	)
	if not any(r.role_profile == ROLE_PROFILE for r in user.role_profiles):
		user.append("role_profiles", {"role_profile": ROLE_PROFILE})
	user.flags.no_welcome_mail = True
	user.save(ignore_permissions=True)
	ctx.count("User", not exists)

	from frappe.utils.password import update_password

	update_password(email, ctx.demo_password)
	frappe.defaults.set_user_default("Company", ctx.company, email)
	ctx.log(f"Demo user: {email}")


def cost_open_quotation(ctx):
	name = lookup(ctx, "s4:quotation", "Quotation")
	if name:
		from erpk_demo.api import fill_quotation_costs

		fill_quotation_costs(frappe.get_doc("Quotation", name))
