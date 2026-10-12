"""`bench execute` helpers for running demo sites.

    bench --site <site> execute erpk_demo.tools.harden
    bench --site <site> execute erpk_demo.tools.status
    bench --site <site> execute erpk_demo.tools.process_reposts
"""

import frappe

from erpk_demo.seed import ux


def harden():
	"""Re-apply the database-side hardening from DEPLOY.md §4 (signup off, robots, sessions, passwords)."""
	ux.harden()
	frappe.db.commit()
	if not frappe.conf.get("mute_emails"):
		print("WARNING: mute_emails is not set. Run: bench --site <site> set-config mute_emails 1 --parse")
	print("hardening applied")


def status():
	"""One-screen summary of a demo site: credentials owner, config and key records."""
	user = ux.demo_email()
	conf = frappe.conf
	print(f"site            {frappe.local.site}")
	print(f"demo user       {user} ({'exists' if frappe.db.exists('User', user) else 'MISSING'})")
	print(f"mute_emails     {conf.get('mute_emails')}")
	print(f"target %        {conf.get('erpk_utilisation_target', 80)}")
	print(f"signup disabled {frappe.db.get_single_value('Website Settings', 'disable_signup')}")
	print(f"scheduler       {'disabled' if conf.get('pause_scheduler') or frappe.utils.scheduler.is_scheduler_disabled() else 'enabled'}")
	print(f"emails sent     {frappe.db.count('Email Queue', {'status': 'Sent'})}")
	for dt in ("Work Order", "Sales Order", "Sales Invoice", "Quotation", "Material Request"):
		print(f"{dt:<17} {frappe.db.count(dt, {'docstatus': ['<', 2]})}")


def process_reposts():
	"""Run queued item valuation reposts now (demo sites keep the scheduler off)."""
	from erpk_demo.seed.transactions import process_reposts as run

	run()
	print("reposts processed")
