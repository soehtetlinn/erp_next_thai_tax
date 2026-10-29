# Copyright (c) 2026, Cactus Tree Co.,Ltd and contributors
# For license information, please see license.txt

"""ใบแนบ ภ.ง.ด.1ก: every employee's salary income and tax for the whole tax year (filed by the
end of February of the next year). Built from submitted Salary Slips; see thai_tax/payroll.py."""

import frappe
from frappe import _
from frappe.utils import flt, getdate

from thai_tax.payroll import salary_rows


def execute(filters=None):
	filters = frappe._dict(filters or {})
	year = int(filters.year)
	rows = salary_rows(filters.company, getdate(f"{year}-01-01"), getdate(f"{year}-12-31"))

	certificates = {
		c.employee: c.name
		for c in frappe.get_all(
			"Thai WHT Certificate",
			filters={"company": filters.company, "pnd_form": "ภ.ง.ด.1ก", "docstatus": ["<", 2],
				"posting_date": ["between", [f"{year}-01-01", f"{year}-12-31"]]},
			fields=["employee", "name"],
		)
	}
	for index, row in enumerate(rows, start=1):
		row.sequence = index
		row.condition_code = "1"
		row.certificate = certificates.get(row.employee)

	columns = [
		{"fieldname": "sequence", "label": "ลำดับที่", "fieldtype": "Int", "width": 70},
		{"fieldname": "tax_id", "label": "เลขประจำตัวผู้เสียภาษีอากร", "fieldtype": "Data", "width": 140},
		{"fieldname": "employee_name", "label": "ชื่อผู้มีเงินได้", "fieldtype": "Data", "width": 190},
		{"fieldname": "address", "label": "ที่อยู่ของผู้มีเงินได้", "fieldtype": "Data", "width": 240},
		{"fieldname": "income", "label": "จำนวนเงินได้ทั้งปี", "fieldtype": "Currency", "options": "THB", "width": 140},
		{"fieldname": "tax", "label": "จำนวนเงินภาษีที่หักและนำส่งทั้งปี", "fieldtype": "Currency", "options": "THB", "width": 170},
		{"fieldname": "condition_code", "label": "เงื่อนไข", "fieldtype": "Data", "width": 70},
		{"fieldname": "social_security", "label": "เงินสมทบประกันสังคม", "fieldtype": "Currency", "options": "THB", "width": 130},
		{"fieldname": "provident_fund", "label": "กองทุนสำรองเลี้ยงชีพ", "fieldtype": "Currency", "options": "THB", "width": 130},
		{"fieldname": "certificate", "label": "50 ทวิ", "fieldtype": "Link", "options": "Thai WHT Certificate", "width": 140},
	]
	summary = [
		{"label": _("Tax Year"), "value": f"{year + 543} ({year})", "datatype": "Data"},
		{"label": _("Employees"), "value": len(rows), "datatype": "Int"},
		{"label": _("Total Income 40(1)"), "value": sum(flt(r.income) for r in rows), "datatype": "Currency", "currency": "THB"},
		{"label": _("Total Tax Withheld"), "value": sum(flt(r.tax) for r in rows), "datatype": "Currency", "currency": "THB", "indicator": "Red"},
	]
	missing = [r.employee_name for r in rows if not r.tax_id]
	message = _("Add a Thai Tax ID on these employees: {0}").format(", ".join(missing)) if missing else None
	return columns, rows, message, None, summary
