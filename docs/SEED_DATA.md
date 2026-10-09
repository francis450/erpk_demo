# SEED_DATA — furniture profile

All figures are **sample** data, plausible for a Nairobi solid-wood furniture maker.
Put every value below in `seed/profiles/furniture.py` as plain data structures.
After seeding, every finished item's BOM cost must give a **gross margin of 45–70%**
at its standard selling price; if not, adjust hours or prices in the profile and
note it in `docs/DEVIATIONS.md`.

## 1. Company
| Field | Value |
| --- | --- |
| Name | from `company` arg, e.g. `Tira Studio (Demo)` |
| Abbr | from `abbr` arg, e.g. `TSD` |
| Country / currency | Kenya / KES |
| Default warehouse names | see SPEC §3 |

## 2. UOMs
Create if missing: `Board Foot` (BF, whole number off), `Sheet`, `Pair`, `Pack`.
Use existing `Nos`, `Kg`, `Litre`, `Meter` (check exact v16 names).

## 3. Item groups
`Timber`, `Sheet Materials`, `Upholstery`, `Hardware`, `Finishes & Consumables`,
`Furniture` (finished), `Bespoke Furniture`, `Workshop Scrap` — all under `All Item Groups`.

## 4. Raw materials (stock items, warehouse = Maragua Workshop – Raw Materials)
| Code | Name | Group | UOM | Valuation rate (KES) | Opening qty | Reorder level | Reorder qty |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TMB-MG1 | Mango Wood Board 1" | Timber | Board Foot | 160 | 900 | 250 | 600 |
| TMB-MG2 | Mango Wood Board 2" | Timber | Board Foot | 220 | 1,400 | 400 | 800 |
| SHT-PLY18 | Plywood 18mm (8×4) | Sheet Materials | Sheet | 4,800 | 40 | 10 | 30 |
| UPH-LIN-OAT | Linen Upholstery Fabric – Oat | Upholstery | Meter | 1,200 | **14** | 30 | 80 |
| UPH-FOAM2 | High-Density Foam 2" | Upholstery | Sheet | 3,500 | 25 | 8 | 20 |
| UPH-WEB | Upholstery Webbing | Upholstery | Meter | 90 | 300 | 80 | 200 |
| HW-SCR | Wood Screws (box of 200) | Hardware | Pack | 350 | 60 | 15 | 40 |
| HW-RUN | Drawer Runners, soft-close | Hardware | Pair | 900 | 50 | 12 | 40 |
| HW-HNG | Concealed Hinges | Hardware | Pair | 250 | 80 | 20 | 60 |
| HW-BRK | Bed Bracket Set | Hardware | Pack | 1,100 | 20 | 6 | 15 |
| FIN-GLUE | Wood Glue (PVA) | Finishes & Consumables | Litre | 650 | 40 | 10 | 30 |
| FIN-OIL | Hardwax Oil Finish | Finishes & Consumables | Litre | 1,800 | 30 | 8 | 20 |
| FIN-SAND | Sandpaper Sheet (assorted grit) | Finishes & Consumables | Nos | 40 | 600 | 150 | 400 |

`UPH-LIN-OAT` starts **below** its reorder level on purpose (story 3).

## 5. Scrap items (non-sales stock items, group Workshop Scrap)
| Code | Name | UOM | Valuation rate |
| --- | --- | --- | --- |
| SCR-OFFCUT | Mango Wood Offcuts | Board Foot | 40 |
| SCR-DUST | Sawdust | Kg | 5 |

## 6. Workstations and operations
| Workstation | Hour rate (KES) | Operation |
| --- | --- | --- |
| Cutting & Planing | 1,200 | Cutting & Planing |
| Joinery Bench | 1,500 | Joinery |
| Sanding Bay | 900 | Sanding |
| Finishing Booth | 1,000 | Finishing |
| Upholstery Bench | 1,300 | Upholstery |

## 7. Finished goods (group Furniture, sales items, default warehouse Maragua Workshop – Finished Goods)
| Code | Name | Std selling price (KES) |
| --- | --- | --- |
| DT-6S | Mango Wood Dining Table, 6-seater (1.8 m) | 145,000 |
| BED-KG | Mango Wood King Bed (6×6) | 165,000 |
| CT-RND | Round Coffee Table (90 cm) | 45,000 |
| SOFA-3S | 3-Seater Sofa, Linen Oat | 185,000 |
| TV-180 | TV Stand with Drawers (1.8 m) | 78,000 |

Price List `Standard Selling` (KES); also `Standard Buying` with raw material rates.

## 8. BOMs (quantity 1, with operations, scrap items)
Quantities per finished piece. Hours are operation time in minutes ÷ 60.

**DT-6S**
- TMB-MG2 38 BF · TMB-MG1 16 BF · FIN-GLUE 0.5 L · FIN-OIL 1 L · FIN-SAND 20 · HW-SCR 1
- Ops: Cutting 4 h · Joinery 14 h · Sanding 6 h · Finishing 5 h
- Scrap: SCR-OFFCUT 10 BF · SCR-DUST 6 kg

**BED-KG**
- TMB-MG2 46 BF · TMB-MG1 22 BF · SHT-PLY18 2 · HW-BRK 1 · HW-SCR 1 · FIN-GLUE 0.5 · FIN-OIL 1.2 · FIN-SAND 24
- Ops: Cutting 5 h · Joinery 14 h · Sanding 7 h · Finishing 6 h
- Scrap: SCR-OFFCUT 13 BF · SCR-DUST 8 kg

**CT-RND**
- TMB-MG2 12 BF · TMB-MG1 4 BF · FIN-GLUE 0.2 · FIN-OIL 0.4 · FIN-SAND 8
- Ops: Cutting 1.5 h · Joinery 4 h · Sanding 2.5 h · Finishing 2 h
- Scrap: SCR-OFFCUT 3.5 BF · SCR-DUST 2 kg

**SOFA-3S**
- TMB-MG1 24 BF · SHT-PLY18 1 · UPH-LIN-OAT 14 m · UPH-FOAM2 4 · UPH-WEB 25 m · HW-SCR 1 · FIN-GLUE 0.4 · FIN-OIL 0.5 · FIN-SAND 10
- Ops: Cutting 3 h · Joinery 8 h · Sanding 3 h · Finishing 2 h · Upholstery 12 h
- Scrap: SCR-OFFCUT 5 BF · SCR-DUST 3 kg

**TV-180**
- TMB-MG2 26 BF · TMB-MG1 10 BF · SHT-PLY18 1 · HW-RUN 3 · HW-HNG 2 · HW-SCR 1 · FIN-GLUE 0.3 · FIN-OIL 0.8 · FIN-SAND 14
- Ops: Cutting 3 h · Joinery 9 h · Sanding 4 h · Finishing 4 h
- Scrap: SCR-OFFCUT 7 BF · SCR-DUST 4 kg

Check margins after BOM cost update (target 45–70%); tune hours, not prices.

## 9. Parties
Customers (group Individual or Commercial, territory Kenya), all suffixed "(Demo)":
- `Achieng Otieno (Demo)` — individual, bespoke dining table buyer
- `Kimani & Co. Interiors (Demo)` — commercial, bespoke projects
- `Walk-in Showroom Customer (Demo)` — individual
- `Lavington Residence (Demo)` — individual

Suppliers: `Muranga Timber Yard (Demo)` (timber), `Nairobi Fabric House (Demo)`
(upholstery), `Industrial Area Hardware (Demo)` (hardware, finishes).
Set default supplier per raw material.

## 10. Opening stock (posting date = today − 120 days)
- Raw materials per §4 via Stock Reconciliation (Opening Stock) into Raw Materials.
- Finished goods: DT-6S 2 and CT-RND 3 at Ngong Road Showroom; TV-180 1 and BED-KG 1
  at Redhill Showroom; SOFA-3S 1 at Ngong Road. Valuation = BOM unit cost.
- Then update BOM costs (BOM Update Tool or `update_cost`) and submit BOMs.

## 11. History (gives the utilisation chart a story)
Create and fully complete Work Orders backdated across the last ~4 months, in
chronological order. For each: Material Transfer for Manufacture → Manufacture
Stock Entry with **actual** timber consumed and offcuts that differ from the BOM, so
utilisation improves over time:

| Month (relative) | Work orders (item × qty) | Target utilisation that month |
| --- | --- | --- |
| −4 | DT-6S×2, CT-RND×3 | ~72% |
| −3 | BED-KG×1, TV-180×2, CT-RND×2 | ~75% |
| −2 | DT-6S×2, SOFA-3S×1, TV-180×1 | ~78% |
| −1 | DT-6S×1, BED-KG×2, CT-RND×2 | ~81% |
| current | covered by stories below | ~79% (just under target) |

Adjust offcut quantities on the Manufacture entries to hit those utilisation
figures. After each manufacture, move most finished pieces to a showroom via
Material Transfer and sell a portion via Sales Invoice (update stock) to a demo
customer, so stock balances and sales history look alive. Keep showroom stock
small (0–3 per item).

## 12. Demo stories (current month)
**Story 1 — Bespoke table, complete.**
- Create item `BSP-0001` "Bespoke Mango Dining Table 2.2 m – Achieng Otieno" (group
  Bespoke Furniture), BOM copied from DT-6S with timber ×1.25 and hours ×1.2.
- Quotation (to Achieng Otieno) at KES 185,000, submitted → Sales Order
  (delivery date = 3 days ago) → Work Order → transfer → Job Cards completed →
  Manufacture with offcuts giving ~79% utilisation → Material Transfer to Ngong
  Road Showroom → Delivery Note from Ngong Road → Sales Invoice → 50% deposit
  Payment Entry (Mode: Bank Transfer) recorded earlier, balance paid on delivery.

**Story 2 — King bed, in progress.**
- Sales Order to `Lavington Residence (Demo)` for BED-KG at KES 165,000, delivery
  date = today + 10 days → Work Order → Material Transfer done → Job Cards:
  Cutting completed, Joinery in progress (partially logged time), the rest open.

**Story 3 — Fabric shortage.**
- `UPH-LIN-OAT` stock is 14 m, below its reorder level of 30.
- Sales Order to `Kimani & Co. Interiors (Demo)` for SOFA-3S × 2 (needs 28 m),
  delivery in 14 days, Work Order created but not started.
- Run the reorder logic (`erpnext.stock.reorder_item.reorder_item` — verify path in
  v16) or create the Material Request (Purchase, 80 m, supplier Nairobi Fabric House)
  so the shortage is visible as a draft-able purchase before the floor runs out.

**Story 4 — Open quotation for the walkthrough.**
- Draft Quotation to `Kimani & Co. Interiors (Demo)` with DT-6S ×1 at 145,000 and
  TV-180 ×2 at 68,000 (discounted) so the margin colours show green and orange.
  Leave in Draft so the prospect can edit prices and watch margins move.

## 13. Final state checks (seed asserts these, logs warnings if false)
- 5 finished items, 1 bespoke item, 13 raw materials, 2 scrap items.
- 6 warehouses with non-zero stock in at least 4.
- ≥ 14 completed Work Orders, 1 in progress, 1 not started.
- Wood Utilisation report returns ≥ 5 months of data, last full month ≥ 80%.
- 1 Material Request for UPH-LIN-OAT.
- 1 draft Quotation with cost + margin populated on every row.
