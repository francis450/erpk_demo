frappe.query_reports["Wood Utilisation"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			// first day of the month five months back (month_start() takes no argument)
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -5).slice(0, 8) + "01",
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "work_order",
			label: __("Work Order"),
			fieldtype: "Link",
			options: "Work Order",
		},
		{
			fieldname: "group_by",
			label: __("Group By"),
			fieldtype: "Select",
			options: ["Month", "Work Order"],
			default: "Month",
		},
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (data && ["utilisation", "variance"].includes(column.fieldname)) {
			const color = data.variance >= 0 ? "var(--green-600)" : "var(--orange-600)";
			value = `<span style="color:${color};font-weight:600">${value}</span>`;
		}
		return value;
	},
};
