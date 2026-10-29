# Copyright (c) 2026, Cactus Tree Co.,Ltd and contributors
# For license information, please see license.txt

"""ใบแนบ ภ.ง.ด.3 / ภ.ง.ด.53: the month's withholding, one line per income item, in the order
and with the columns of the Revenue Department's attachment sheet. Export it to Excel to copy
into RD Prep or the e-Filing site, or print it as the attachment for a paper filing."""

import frappe
from frappe import _
from frappe.utils import flt, get_last_day, getdate

from thai_tax.utils import thai_date, thai_month


def execute(filters=None):
	filters = frappe._dict(filters or {})
	start = getdate(f"{filters.year}-{int(filters.month):02d}-01")
	end = get_last_day(start)

	rows = frappe.db.sql(
		"""
		select c.name as certificate, c.payee_tax_id, c.payee_branch, c.payee_name, c.payee_address,
			c.condition, i.paid_date, i.income_category, i.description, i.rate, i.amount, i.tax_amount
		from `tabThai WHT Certificate` c
		join `tabThai WHT Certificate Item` i on i.parent = c.name
		where c.docstatus = 1 and c.company = %(company)s and c.pnd_form = %(pnd_form)s
			and c.posting_date between %(start)s and %(end)s
		order by c.posting_date, c.name, i.idx
		""",
		{"company": filters.company, "pnd_form": filters.pnd_form, "start": start, "end": end},
		as_dict=True,
	)

	sequence = {}
	for row in rows:
		# ลำดับที่ counts payees' certificates, not item lines
		row.sequence = sequence.setdefault(row.certificate, len(sequence) + 1)
		row.paid_date_th = thai_date(row.paid_date, short=True)
		row.income = row.description or row.income_category
		row.condition_code = (row.condition or "1")[0]

	total_amount = sum(flt(r.amount) for r in rows)
	total_tax = sum(flt(r.tax_amount) for r in rows)
	period = f"{thai_month(start.month)} {start.year + 543}"

	summary = [
		{"label": _("Period"), "value": period, "datatype": "Data"},
		{"label": _("Payees"), "value": len(sequence), "datatype": "Int"},
		{"label": _("Total Paid"), "value": total_amount, "datatype": "Currency", "currency": "THB"},
		{"label": _("Total Tax to Remit"), "value": total_tax, "datatype": "Currency", "currency": "THB", "indicator": "Red"},
	]
	return columns(filters.pnd_form), rows, None, None, summary


def columns(pnd_form):
	cols = [
		{"fieldname": "sequence", "label": "ลำดับที่", "fieldtype": "Int", "width": 70},
		{"fieldname": "payee_tax_id", "label": "เลขประจำตัวผู้เสียภาษีอากร", "fieldtype": "Data", "width": 140},
	]
	if pnd_form == "ภ.ง.ด.53":
		cols.append({"fieldname": "payee_branch", "label": "สาขาที่", "fieldtype": "Data", "width": 70})
	cols += [
		{"fieldname": "payee_name", "label": "ชื่อผู้มีเงินได้", "fieldtype": "Data", "width": 200},
		{"fieldname": "payee_address", "label": "ที่อยู่", "fieldtype": "Data", "width": 240},
		{"fieldname": "paid_date_th", "label": "วันเดือนปีที่จ่าย", "fieldtype": "Data", "width": 100},
		{"fieldname": "income", "label": "ประเภทเงินได้พึงประเมินที่จ่าย", "fieldtype": "Data", "width": 160},
		{"fieldname": "rate", "label": "อัตราภาษีร้อยละ", "fieldtype": "Percent", "width": 90},
		{"fieldname": "amount", "label": "จำนวนเงินที่จ่าย", "fieldtype": "Currency", "options": "THB", "width": 130},
		{"fieldname": "tax_amount", "label": "จำนวนเงินภาษีที่หักและนำส่ง", "fieldtype": "Currency", "options": "THB", "width": 140},
		{"fieldname": "condition_code", "label": "เงื่อนไข", "fieldtype": "Data", "width": 70},
		{"fieldname": "certificate", "label": "50 ทวิ", "fieldtype": "Link", "options": "Thai WHT Certificate", "width": 140},
	]
	return cols
