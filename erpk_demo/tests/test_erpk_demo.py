"""Run on a seeded test site:  bench --site <test site> run-tests --app erpk_demo"""

import os
import subprocess

import frappe
from frappe.tests import IntegrationTestCase

from erpk_demo.api import get_item_unit_cost
from erpk_demo.erpk_demo.report.wood_utilisation.wood_utilisation import summarise, timber_group, timber_uom

APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def seeded_company():
	return frappe.conf.get("erpk_demo_test_company") or frappe.db.get_single_value(
		"Global Defaults", "default_company"
	)


class TestUnitCost(IntegrationTestCase):
	def test_returns_bom_unit_cost(self):
		bom = frappe.get_all(
			"BOM",
			filters={"is_default": 1, "is_active": 1, "docstatus": 1},
			fields=["item", "company", "total_cost", "quantity"],
			limit=1,
		)
		if not bom:
			self.skipTest("site not seeded")
		bom = bom[0]
		self.assertAlmostEqual(get_item_unit_cost(bom.item, bom.company), bom.total_cost / bom.quantity, places=2)

	def test_falls_back_to_valuation_rate_then_zero(self):
		item = frappe.get_all(
			"Item",
			filters={"is_stock_item": 1, "name": ["not in", frappe.get_all("BOM", pluck="item") or [""]]},
			fields=["name", "valuation_rate"],
			limit=1,
		)
		if item:
			self.assertGreaterEqual(get_item_unit_cost(item[0].name), 0)
		self.assertEqual(get_item_unit_cost(""), 0)


class TestWoodUtilisation(IntegrationTestCase):
	def test_known_manufacture_entry(self):
		"""50 BF timber issued, 10 BF offcuts back, 5 kg sawdust -> 80%, sawdust not counted."""
		uom, group = timber_uom(), timber_group()
		date = frappe.utils.getdate("2026-03-15")
		base = {"posting_date": date, "work_order": "WO-TEST", "stock_entry": "SE-TEST", "is_finished_item": 0}
		rows = [
			frappe._dict(base, item_code="TIMBER-A", s_warehouse="RM", t_warehouse=None, item_group=group, transfer_qty=30, stock_uom=uom, secondary_item_type=None),
			frappe._dict(base, item_code="TIMBER-B", s_warehouse="RM", t_warehouse=None, item_group=group, transfer_qty=20, stock_uom=uom, secondary_item_type=None),
			frappe._dict(base, item_code="GLUE", s_warehouse="RM", t_warehouse=None, item_group="Other", transfer_qty=1, stock_uom="Litre", secondary_item_type=None),
			frappe._dict(base, item_code="OFFCUT", s_warehouse=None, t_warehouse="SCRAP", item_group="Scrap", transfer_qty=10, stock_uom=uom, secondary_item_type="Scrap"),
			frappe._dict(base, item_code="DUST", s_warehouse=None, t_warehouse="SCRAP", item_group="Scrap", transfer_qty=5, stock_uom="Kg", secondary_item_type="Scrap"),
			frappe._dict(base, item_code="TABLE", s_warehouse=None, t_warehouse="FG", item_group="Furniture", transfer_qty=1, stock_uom="Nos", secondary_item_type=None, is_finished_item=1),
		]
		for group_by in ("Month", "Work Order"):
			(row,) = summarise(rows, group_by)
			self.assertAlmostEqual(row["utilisation"], 80.0)
			self.assertEqual(row["timber_issued"], 50)
			self.assertEqual(row["offcuts"], 10)
			self.assertEqual(row["sawdust"], 5)
			self.assertEqual(row["item_produced"], "TABLE")


class TestSeedIdempotency(IntegrationTestCase):
	def test_second_run_creates_nothing(self):
		company = seeded_company()
		if not (company and frappe.db.exists("BOM", {"company": company, "docstatus": 1})):
			self.skipTest("site not seeded")
		if not frappe.conf.get("erpk_demo_password"):
			self.skipTest("erpk_demo_password not configured")
		from erpk_demo.seed import run

		result = run(profile="furniture", company=company)
		self.assertEqual(result["created"], {})
		self.assertTrue(all(result["checks"].values()), result["checks"])


class TestResetGuard(IntegrationTestCase):
	script = os.path.join(APP_ROOT, "bin", "reset_demo.sh")

	def run_script(self, *args):
		return subprocess.run([self.script, *args], capture_output=True, text=True, timeout=30)

	def test_refuses_site_without_demo(self):
		result = self.run_script("production-site", "--yes")
		self.assertEqual(result.returncode, 3)
		self.assertIn("does not contain 'demo'", result.stderr)

	def test_requires_yes_flag(self):
		result = self.run_script(frappe.local.site) if "demo" in frappe.local.site else None
		if result is None:
			self.skipTest("current site name has no 'demo'")
		self.assertEqual(result.returncode, 5)
