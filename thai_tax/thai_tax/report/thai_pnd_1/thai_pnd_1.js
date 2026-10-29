// Copyright (c) 2026, Cactus Tree Co.,Ltd and contributors
// For license information, please see license.txt

const pnd1_last_month = new Date(new Date().getFullYear(), new Date().getMonth() - 1, 1);

frappe.query_reports["Thai PND 1"] = {
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
			fieldname: "month",
			label: __("Month"),
			fieldtype: "Select",
			options: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12].map(String),
			default: String(pnd1_last_month.getMonth() + 1),
			reqd: 1,
		},
		{
			fieldname: "year",
			label: __("Year (A.D.)"),
			fieldtype: "Int",
			default: pnd1_last_month.getFullYear(),
			reqd: 1,
		},
	],
};
