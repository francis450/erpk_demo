"""Seed a prospect demo onto a site.

    bench --site <site> execute erpk_demo.seed.run \
      --kwargs "{'profile': 'furniture', 'company': '<Company>', 'abbr': '<ABBR>'}"

Every phase is idempotent and commits on its own, so a failed run can simply be re-run.
"""

import importlib

import frappe

from erpk_demo.seed.common import Ctx

PHASES = ("masters", "opening", "history", "stories", "ux")


def run(profile="furniture", company=None, abbr=None, demo_password=None, phases=None):
	if not company:
		frappe.throw("company is required")

	demo_password = demo_password or frappe.conf.get("erpk_demo_password")
	if not demo_password:
		frappe.throw("Pass demo_password or set erpk_demo_password in site config")

	ctx = Ctx(
		profile=load_profile(profile),
		profile_name=profile,
		company=company,
		abbr=abbr or default_abbr(company),
		demo_password=demo_password,
	)

	frappe.flags.mute_emails = True
	frappe.flags.in_demo_seed = True
	try:
		for phase in phases or PHASES:
			ctx.log(f"── phase: {phase}")
			_phase_fn(phase)(ctx)
			frappe.db.commit()
	finally:
		frappe.flags.in_demo_seed = False

	ctx.print_summary()
	from erpk_demo.seed.checks import final_checks

	return final_checks(ctx)


def load_profile(name):
	return importlib.import_module(f"erpk_demo.seed.profiles.{name}")


def default_abbr(company):
	"""Initials of the company name, ignoring anything in brackets."""
	name = company.split("(")[0]
	return "".join(w[0] for w in name.split() if w[0].isalnum()).upper()


def _phase_fn(phase):
	from erpk_demo.seed import masters, transactions, ux

	return {
		"masters": masters.run,
		"opening": transactions.opening,
		"history": transactions.history,
		"stories": transactions.stories,
		"ux": ux.run,
	}[phase]
