// Copyright (c) 2026, Cactus Tree Co.,Ltd and contributors
// For license information, please see license.txt

frappe.query_reports["Thai PND 1 Kor"] = {
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
			fieldname: "year",
			label: __("Tax Year (A.D.)"),
			fieldtype: "Int",
			// ภ.ง.ด.1ก is filed in January-February for the year before
			default: new Date().getMonth() < 2 ? new Date().getFullYear() - 1 : new Date().getFullYear(),
			reqd: 1,
		},
	],

	onload(report) {
		report.page.add_inner_button(__("Create Employee 50 Tawi"), () => {
			const { company, year } = report.get_values();
			frappe.call({
				method: "thai_tax.payroll.make_year_end_certificates",
				args: { company, year },
				freeze: true,
				callback: ({ message: r }) => {
					let text = __("Created {0} draft certificates.", [r.created.length]);
					if (r.skipped.length) text += " " + __("{0} employees already had one.", [r.skipped.length]);
					if (r.missing_tax_id.length)
						text += "<br>" + __("No Thai Tax ID, skipped: {0}", [r.missing_tax_id.join(", ")]);
					frappe.msgprint(text, __("Employee 50 Tawi"));
					report.refresh();
				},
			});
		});
	},
};
