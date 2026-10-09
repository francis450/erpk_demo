"""Idempotent helpers shared by the seed phases."""

from collections import defaultdict
from dataclasses import dataclass, field
from types import ModuleType

import frappe


@dataclass
class Ctx:
	profile: ModuleType
	profile_name: str
	company: str
	abbr: str
	demo_password: str
	created: dict = field(default_factory=lambda: defaultdict(int))
	existing: dict = field(default_factory=lambda: defaultdict(int))

	def wh(self, key):
		"""Full warehouse name for a profile warehouse key."""
		return f"{self.profile.WAREHOUSES[key]} - {self.abbr}"

	def acc(self, name):
		"""Account by its (unnumbered) account name in this company."""
		account = frappe.db.get_value("Account", {"account_name": name, "company": self.company, "is_group": 0})
		if not account:
			frappe.throw(f"Account '{name}' not found in {self.company}")
		return account

	def cost_center(self):
		return frappe.get_cached_value("Company", self.company, "cost_center")

	def log(self, msg):
		print(msg)

	def count(self, doctype, was_created):
		(self.created if was_created else self.existing)[doctype] += 1

	def print_summary(self):
		print("\nerpk_demo seed summary (created / already present)")
		for dt in sorted(set(self.created) | set(self.existing)):
			print(f"  {dt:<28} {self.created.get(dt, 0):>4} / {self.existing.get(dt, 0):>4}")
		print(f"  {'TOTAL':<28} {sum(self.created.values()):>4} / {sum(self.existing.values()):>4}")


def ensure_doc(ctx, doctype, filters, values=None, submit=False):
	"""Return the doc matching `filters` (name or dict), inserting it from `values` if missing."""
	name = filters if isinstance(filters, str) else frappe.db.get_value(doctype, filters)
	if name and frappe.db.exists(doctype, name):
		ctx.count(doctype, False)
		doc = frappe.get_doc(doctype, name)
		if submit:
			submit_if_draft(doc)
		return doc

	doc = frappe.get_doc({"doctype": doctype, **(values or {})})
	if isinstance(filters, dict):
		for k, v in filters.items():
			if not doc.get(k):
				doc.set(k, v)
	doc.insert(ignore_permissions=True)
	if submit:
		doc.submit()
	ctx.count(doctype, True)
	return doc


def submit_if_draft(doc):
	if doc.docstatus == 0:
		doc.submit()
	return doc


def find_by_remark(doctype, marker, field="remarks"):
	"""Transactions are keyed on a stable marker in a text field so re-runs find them."""
	return frappe.db.get_value(doctype, {field: ["like", f"%[{marker}]%"], "docstatus": ["<", 2]})


def tag(marker):
	return f"[{marker}]"
