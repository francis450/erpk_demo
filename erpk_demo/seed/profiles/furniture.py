"""Furniture profile: a Nairobi solid mango wood furniture maker.

Plain data only. All figures are SAMPLE data. Every prospect-specific string lives here.
"""

DESCRIPTION = "Solid mango wood furniture maker: workshop in Maragua, showrooms on Ngong Road and at Redhill"

# ── Units, groups ──────────────────────────────────────────────────────────
UOMS = [
	{"uom_name": "Board Foot", "symbol": "BF", "must_be_whole_number": 0},
	{"uom_name": "Sheet", "must_be_whole_number": 1},
	{"uom_name": "Pair", "must_be_whole_number": 1},
	{"uom_name": "Pack", "must_be_whole_number": 1},
]

ITEM_GROUPS = [
	"Timber",
	"Sheet Materials",
	"Upholstery",
	"Hardware",
	"Finishes & Consumables",
	"Furniture",
	"Bespoke Furniture",
	"Workshop Scrap",
]
TIMBER_GROUP = "Timber"
BESPOKE_GROUP = "Bespoke Furniture"
FINISHED_GROUP = "Furniture"

# ── Warehouses (key -> name; created under the company root) ────────────────
WAREHOUSES = {
	"rm": "Maragua Workshop – Raw Materials",
	"wip": "Maragua Workshop – WIP",
	"fg": "Maragua Workshop – Finished Goods",
	"scrap": "Maragua Workshop – Scrap",
	"ngong": "Ngong Road Showroom",
	"redhill": "Redhill Showroom",
}
SHOWROOMS = ("ngong", "redhill")

# ── Parties ─────────────────────────────────────────────────────────────────
CUSTOMERS = {
	"achieng": {"customer_name": "Achieng Otieno (Demo)", "customer_type": "Individual", "customer_group": "Individual"},
	"kimani": {"customer_name": "Kimani & Co. Interiors (Demo)", "customer_type": "Company", "customer_group": "Commercial"},
	"walkin": {"customer_name": "Walk-in Showroom Customer (Demo)", "customer_type": "Individual", "customer_group": "Individual"},
	"lavington": {"customer_name": "Lavington Residence (Demo)", "customer_type": "Individual", "customer_group": "Individual"},
}
TERRITORY = "Kenya"

SUPPLIERS = {
	"timber": {"supplier_name": "Muranga Timber Yard (Demo)", "supplier_group": "Raw Material"},
	"fabric": {"supplier_name": "Nairobi Fabric House (Demo)", "supplier_group": "Raw Material"},
	"hardware": {"supplier_name": "Industrial Area Hardware (Demo)", "supplier_group": "Hardware"},
}

# ── Raw materials ───────────────────────────────────────────────────────────
# code, name, group, uom, valuation rate, opening qty, reorder level, reorder qty, supplier key
RAW_MATERIALS = [
	("TMB-MG1", 'Mango Wood Board 1"', "Timber", "Board Foot", 160, 900, 250, 600, "timber"),
	("TMB-MG2", 'Mango Wood Board 2"', "Timber", "Board Foot", 220, 1400, 400, 800, "timber"),
	("SHT-PLY18", "Plywood 18mm (8×4)", "Sheet Materials", "Sheet", 4800, 40, 10, 30, "timber"),
	("UPH-LIN-OAT", "Linen Upholstery Fabric – Oat", "Upholstery", "Meter", 1200, 14, 30, 80, "fabric"),
	("UPH-FOAM2", 'High-Density Foam 2"', "Upholstery", "Sheet", 3500, 25, 8, 20, "fabric"),
	("UPH-WEB", "Upholstery Webbing", "Upholstery", "Meter", 90, 300, 80, 200, "fabric"),
	("HW-SCR", "Wood Screws (box of 200)", "Hardware", "Pack", 350, 60, 15, 40, "hardware"),
	("HW-RUN", "Drawer Runners, soft-close", "Hardware", "Pair", 900, 50, 12, 40, "hardware"),
	("HW-HNG", "Concealed Hinges", "Hardware", "Pair", 250, 80, 20, 60, "hardware"),
	("HW-BRK", "Bed Bracket Set", "Hardware", "Pack", 1100, 20, 6, 15, "hardware"),
	("FIN-GLUE", "Wood Glue (PVA)", "Finishes & Consumables", "Litre", 650, 40, 10, 30, "hardware"),
	("FIN-OIL", "Hardwax Oil Finish", "Finishes & Consumables", "Litre", 1800, 30, 8, 20, "hardware"),
	("FIN-SAND", "Sandpaper Sheet (assorted grit)", "Finishes & Consumables", "Nos", 40, 600, 150, 400, "hardware"),
]

# ── Scrap (secondary) items ─────────────────────────────────────────────────
SCRAP_ITEMS = [
	("SCR-OFFCUT", "Mango Wood Offcuts", "Board Foot", 40),
	("SCR-DUST", "Sawdust", "Kg", 5),
]
SCRAP_GROUP = "Workshop Scrap"
OFFCUT_ITEM = "SCR-OFFCUT"
DUST_ITEM = "SCR-DUST"

# ── Workstations: hour rate split into operating components (KES / hour) ──
WORKSTATIONS = {
	"Cutting & Planing": {"Wages": 800, "Electricity": 300, "Rent": 100},
	"Joinery Bench": {"Wages": 1200, "Electricity": 150, "Rent": 150},
	"Sanding Bay": {"Wages": 600, "Electricity": 200, "Rent": 100},
	"Finishing Booth": {"Wages": 700, "Electricity": 100, "Rent": 200},
	"Upholstery Bench": {"Wages": 1100, "Electricity": 50, "Rent": 150},
}
# operation -> default workstation
OPERATIONS = {
	"Cutting & Planing": "Cutting & Planing",
	"Joinery": "Joinery Bench",
	"Sanding": "Sanding Bay",
	"Finishing": "Finishing Booth",
	"Upholstery": "Upholstery Bench",
}

# ── Finished goods ──────────────────────────────────────────────────────────
# code, name, standard selling price
FINISHED_GOODS = [
	("DT-6S", "Mango Wood Dining Table, 6-seater (1.8 m)", 145000),
	("BED-KG", "Mango Wood King Bed (6×6)", 165000),
	("CT-RND", "Round Coffee Table (90 cm)", 45000),
	("SOFA-3S", "3-Seater Sofa, Linen Oat", 185000),
	("TV-180", "TV Stand with Drawers (1.8 m)", 78000),
]
MARGIN_TARGET = (45, 70)

# BOMs: per piece. ops are hours; scrap in item UOM.
BOMS = {
	"DT-6S": {
		"items": {"TMB-MG2": 38, "TMB-MG1": 16, "FIN-GLUE": 0.5, "FIN-OIL": 1, "FIN-SAND": 20, "HW-SCR": 1},
		"ops": {"Cutting & Planing": 4, "Joinery": 14, "Sanding": 6, "Finishing": 5},
		"scrap": {"SCR-OFFCUT": 10, "SCR-DUST": 6},
	},
	"BED-KG": {
		"items": {
			"TMB-MG2": 46, "TMB-MG1": 22, "SHT-PLY18": 2, "HW-BRK": 1, "HW-SCR": 1,
			"FIN-GLUE": 0.5, "FIN-OIL": 1.2, "FIN-SAND": 24,
		},
		"ops": {"Cutting & Planing": 5, "Joinery": 14, "Sanding": 7, "Finishing": 6},
		"scrap": {"SCR-OFFCUT": 13, "SCR-DUST": 8},
	},
	"CT-RND": {
		"items": {"TMB-MG2": 12, "TMB-MG1": 4, "FIN-GLUE": 0.2, "FIN-OIL": 0.4, "FIN-SAND": 8},
		"ops": {"Cutting & Planing": 1.5, "Joinery": 4, "Sanding": 2.5, "Finishing": 2},
		"scrap": {"SCR-OFFCUT": 3.5, "SCR-DUST": 2},
	},
	"SOFA-3S": {
		"items": {
			"TMB-MG1": 24, "SHT-PLY18": 1, "UPH-LIN-OAT": 14, "UPH-FOAM2": 4, "UPH-WEB": 25,
			"HW-SCR": 1, "FIN-GLUE": 0.4, "FIN-OIL": 0.5, "FIN-SAND": 10,
		},
		"ops": {"Cutting & Planing": 3, "Joinery": 8, "Sanding": 3, "Finishing": 2, "Upholstery": 12},
		"scrap": {"SCR-OFFCUT": 5, "SCR-DUST": 3},
	},
	"TV-180": {
		"items": {
			"TMB-MG2": 26, "TMB-MG1": 10, "SHT-PLY18": 1, "HW-RUN": 3, "HW-HNG": 2, "HW-SCR": 1,
			"FIN-GLUE": 0.3, "FIN-OIL": 0.8, "FIN-SAND": 14,
		},
		"ops": {"Cutting & Planing": 3, "Joinery": 9, "Sanding": 4, "Finishing": 4},
		"scrap": {"SCR-OFFCUT": 7, "SCR-DUST": 4},
	},
}

# ── Opening stock (days before today) ───────────────────────────────────────
OPENING_DAYS_AGO = 120
OPENING_FINISHED = [("DT-6S", "ngong", 2), ("CT-RND", "ngong", 3), ("SOFA-3S", "ngong", 1), ("TV-180", "redhill", 1), ("BED-KG", "redhill", 1)]

# ── History: completed work orders, one per piece, by month offset ──────────
# Each month: target utilisation %, timber over-issue factor vs BOM,
# work orders (item, day of month, destination), sales (customer, item, qty, from, day).
HISTORY = {
	-4: {
		"utilisation": 72, "timber_factor": 1.06,
		"work_orders": [("DT-6S", 14, "ngong"), ("DT-6S", 17, "redhill"), ("CT-RND", 19, "ngong"), ("CT-RND", 21, "ngong"), ("CT-RND", 23, "redhill")],
		"sales": [("walkin", "CT-RND", 2, "ngong", 26), ("lavington", "DT-6S", 1, "ngong", 28)],
	},
	-3: {
		"utilisation": 75, "timber_factor": 1.04,
		"work_orders": [("BED-KG", 6, "redhill"), ("TV-180", 10, "ngong"), ("TV-180", 14, "redhill"), ("CT-RND", 17, "ngong"), ("CT-RND", 20, "redhill")],
		"sales": [("kimani", "TV-180", 1, "redhill", 22), ("walkin", "CT-RND", 2, "ngong", 25), ("walkin", "BED-KG", 1, "redhill", 28)],
	},
	-2: {
		"utilisation": 78, "timber_factor": 1.03,
		"work_orders": [("DT-6S", 5, "ngong"), ("DT-6S", 11, "ngong"), ("SOFA-3S", 15, "ngong"), ("TV-180", 19, "redhill")],
		"sales": [("kimani", "DT-6S", 2, "ngong", 22), ("lavington", "SOFA-3S", 1, "ngong", 25), ("walkin", "TV-180", 1, "redhill", 27)],
		# fabric bought before the sofa build so the shortage story still starts at the opening level
		"purchases": [("fabric", "UPH-LIN-OAT", 14, 12)],
	},
	-1: {
		"utilisation": 81, "timber_factor": 1.01,
		"work_orders": [("DT-6S", 4, "redhill"), ("BED-KG", 9, "ngong"), ("BED-KG", 15, "redhill"), ("CT-RND", 19, "fg"), ("CT-RND", 22, "ngong")],
		"sales": [("walkin", "DT-6S", 1, "redhill", 24), ("kimani", "BED-KG", 1, "redhill", 26), ("walkin", "CT-RND", 1, "ngong", 27)],
	},
}
# Per-work-order wobble around the month's utilisation target (percentage points)
UTILISATION_JITTER = [-0.8, 0.6, -0.3, 0.9, -0.4]
# Sawdust per piece varies with the same factor as timber
UNPAID_HISTORY_CUSTOMERS = ("kimani",)  # last month's invoice to these stays outstanding

# ── Demo stories (current month) ────────────────────────────────────────────
BESPOKE = {
	"item_code": "BSP-0001",
	"item_name": "Bespoke Mango Dining Table 2.2 m – Achieng Otieno",
	"base_item": "DT-6S",
	"timber_factor": 1.25,
	"hours_factor": 1.2,
	"customer": "achieng",
	"rate": 185000,
	"utilisation": 79,
	"deliver_from": "ngong",
	"deposit_pct": 50,
	"mode_of_payment": "Bank Transfer",
}
IN_PROGRESS = {"customer": "lavington", "item_code": "BED-KG", "rate": 165000, "delivery_in_days": 10}
SHORTAGE = {
	"customer": "kimani",
	"item_code": "SOFA-3S",
	"qty": 2,
	"rate": 185000,
	"delivery_in_days": 14,
	"material": "UPH-LIN-OAT",
	"supplier": "fabric",
}
OPEN_QUOTATION = {"customer": "kimani", "items": [("DT-6S", 1, 145000), ("TV-180", 2, 68000)]}

# ── Workspace "Start here" links (label, link key resolved by the seed) ─────
START_HERE = [
	("See what a dining table really costs", "bom:DT-6S"),
	("Price a custom order and see the margin", "open_quotation"),
	("Follow a bespoke table from order to delivery", "bespoke_sales_order"),
	("Check stock at the workshop and both showrooms", "stock_balance"),
	("See shortages before they reach the floor", "shortage_material_request"),
	("Track wood utilisation against the 80% goal", "wood_utilisation"),
]
