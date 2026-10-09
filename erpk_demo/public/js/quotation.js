// Est. unit cost and margin while pricing a quotation. Internal only: hidden on print.
(() => {
	const BANDS = [
		[30, "var(--red-600)"],
		[45, "var(--orange-600)"],
		[Infinity, "var(--green-600)"],
	];
	const cost_cache = {};

	const margin_color = (pct) => BANDS.find(([upper]) => pct < upper)[1];

	const colour_margin = (value, df) => {
		const pct = parseFloat(String(value).replace(/<[^>]*>|[^0-9.\-]/g, ""));
		if (isNaN(pct)) return value;
		return `<span style="color:${margin_color(pct)};font-weight:600">${value}</span>`;
	};

	const install_formatters = () => {
		for (const dt of ["Quotation Item", "Quotation"]) {
			const df = frappe.meta.docfield_map[dt]?.erpk_margin_pct;
			if (df) df.formatter = colour_margin;
		}
	};

	const unit_cost = async (frm, item_code) => {
		const key = `${frm.doc.company}::${item_code}`;
		if (!(key in cost_cache)) {
			cost_cache[key] = await frappe.xcall("erpk_demo.api.get_item_unit_cost", {
				item_code,
				company: frm.doc.company,
			});
		}
		return cost_cache[key];
	};

	const margin = (net, cost) => (net ? ((net - cost) / net) * 100 : 0);

	const recompute = frappe.utils.debounce(async (frm) => {
		if (frm.doc.docstatus !== 0) return;
		let total_cost = 0;
		let total_net = 0;
		for (const row of frm.doc.items || []) {
			if (!row.item_code) continue;
			const cost = await unit_cost(frm, row.item_code);
			const net = flt(row.net_amount || row.amount);
			const row_cost = cost * flt(row.qty);
			row.erpk_unit_cost = cost;
			row.erpk_margin_pct = margin(net, row_cost);
			total_cost += row_cost;
			total_net += net;
		}
		frm.doc.erpk_total_cost = total_cost;
		frm.doc.erpk_margin_pct = margin(total_net, total_cost);
		frm.refresh_field("items");
		frm.refresh_field("erpk_total_cost");
		frm.refresh_field("erpk_margin_pct");
		frm.dirty();
		show_indicator(frm);
	}, 400);

	const show_indicator = (frm) => {
		if (!frm.doc.erpk_total_cost || frm.doc.docstatus !== 0) return;
		const pct = flt(frm.doc.erpk_margin_pct);
		const color = pct < 30 ? "red" : pct < 45 ? "orange" : "green";
		frm.dashboard.clear_headline();
		frm.dashboard.set_headline(
			`<span class="indicator ${color}">${__("Est. margin {0}% on cost {1}", [
				format_number(pct, null, 1),
				format_currency(frm.doc.erpk_total_cost, frm.doc.currency),
			])}</span>`
		);
	};

	frappe.ui.form.on("Quotation", {
		setup: install_formatters,
		onload: install_formatters,
		refresh(frm) {
			install_formatters();
			show_indicator(frm);
		},
		company: recompute,
		discount_amount: recompute,
		additional_discount_percentage: recompute,
		items_remove: recompute,
	});

	frappe.ui.form.on("Quotation Item", {
		item_code: (frm) => recompute(frm),
		qty: (frm) => recompute(frm),
		rate: (frm) => recompute(frm),
		price_list_rate: (frm) => recompute(frm),
		discount_percentage: (frm) => recompute(frm),
		discount_amount: (frm) => recompute(frm),
	});
})();
