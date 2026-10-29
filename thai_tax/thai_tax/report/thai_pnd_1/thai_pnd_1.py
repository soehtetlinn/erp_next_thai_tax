# Copyright (c) 2026, Cactus Tree Co.,Ltd and contributors
# For license information, please see license.txt

"""ใบแนบ ภ.ง.ด.1: salary withholding for one month (due by the 7th of the next month, or the 15th
online). Built from submitted Salary Slips; see thai_tax/payroll.py."""

import frappe
from frappe import _
from frappe.utils import flt, get_last_day, getdate

from thai_tax.payroll import salary_rows
from thai_tax.utils import thai_date, thai_month


def execute(filters=None):
	filters = frappe._dict(filters or {})
	start = getdate(f"{filters.year}-{int(filters.month):02d}-01")
	rows = salary_rows(filters.company, start, get_last_day(start))
	for index, row in enumerate(rows, start=1):
		row.sequence = index
		row.paid_date_th = thai_date(row.paid_date, short=True)
		row.condition_code = "1"

	columns = [
		{"fieldname": "sequence", "label": "ลำดับที่", "fieldtype": "Int", "width": 70},
		{"fieldname": "tax_id", "label": "เลขประจำตัวผู้เสียภาษีอากร", "fieldtype": "Data", "width": 140},
		{"fieldname": "employee_name", "label": "ชื่อผู้มีเงินได้", "fieldtype": "Data", "width": 200},
		{"fieldname": "paid_date_th", "label": "วันเดือนปีที่จ่าย", "fieldtype": "Data", "width": 110},
		{"fieldname": "income", "label": "จำนวนเงินได้ที่จ่ายในครั้งนี้", "fieldtype": "Currency", "options": "THB", "width": 150},
		{"fieldname": "tax", "label": "จำนวนเงินภาษีที่หักและนำส่งในครั้งนี้", "fieldtype": "Currency", "options": "THB", "width": 170},
		{"fieldname": "condition_code", "label": "เงื่อนไข", "fieldtype": "Data", "width": 70},
		{"fieldname": "employee", "label": _("Employee"), "fieldtype": "Link", "options": "Employee", "width": 120},
	]
	summary = [
		{"label": _("Period"), "value": f"{thai_month(start.month)} {start.year + 543}", "datatype": "Data"},
		{"label": _("Employees"), "value": len(rows), "datatype": "Int"},
		{"label": _("Total Income 40(1)"), "value": sum(flt(r.income) for r in rows), "datatype": "Currency", "currency": "THB"},
		{"label": _("Total Tax to Remit"), "value": sum(flt(r.tax) for r in rows), "datatype": "Currency", "currency": "THB", "indicator": "Red"},
	]
	missing = [r.employee_name for r in rows if not r.tax_id]
	message = _("Add a Thai Tax ID on these employees: {0}").format(", ".join(missing)) if missing else None
	return columns, rows, message, None, summary
