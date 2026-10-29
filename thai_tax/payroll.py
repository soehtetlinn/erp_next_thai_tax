"""Salary withholding (มาตรา 40 (1)) from Frappe HR payroll: ภ.ง.ด.1 each month, ภ.ง.ด.1ก for the
year, and each employee's year-end 50 ทวิ.

Income is the gross pay of submitted Salary Slips, dated by the slip's posting date. Tax is the
deduction components marked "Is Income Tax Component"; social security and provident fund are the
components whose Thai Fund Type says so.
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate

from thai_tax.constants import CONDITIONS

SOCIAL_SECURITY = "Social Security"
PROVIDENT_FUND = "Provident Fund"


def salary_rows(company: str, start, end) -> list[frappe._dict]:
	"""One row per employee for slips posted between start and end."""
	rows = frappe.db.sql(
		"""
		select ss.employee, ss.employee_name,
			sum(ss.base_gross_pay) as income,
			max(ss.posting_date) as paid_date,
			sum(coalesce(d.tax, 0)) as tax,
			sum(coalesce(d.social_security, 0)) as social_security,
			sum(coalesce(d.provident_fund, 0)) as provident_fund
		from `tabSalary Slip` ss
		left join (
			select sd.parent,
				sum(case when sc.is_income_tax_component = 1 then sd.amount else 0 end) as tax,
				sum(case when sc.thai_fund_type = %(ss)s then sd.amount else 0 end) as social_security,
				sum(case when sc.thai_fund_type = %(pf)s then sd.amount else 0 end) as provident_fund
			from `tabSalary Detail` sd
			join `tabSalary Component` sc on sc.name = sd.salary_component
			where sd.parenttype = 'Salary Slip' and sd.parentfield = 'deductions'
			group by sd.parent
		) d on d.parent = ss.name
		where ss.docstatus = 1 and ss.company = %(company)s and ss.posting_date between %(start)s and %(end)s
		group by ss.employee, ss.employee_name
		order by ss.employee
		""",
		{"company": company, "start": start, "end": end, "ss": SOCIAL_SECURITY, "pf": PROVIDENT_FUND},
		as_dict=True,
	)
	info = {
		e.name: e
		for e in frappe.get_all(
			"Employee",
			filters={"name": ["in", [r.employee for r in rows] or [""]]},
			fields=["name", "thai_tax_id", "salutation", "first_name", "last_name", "current_address", "permanent_address"],
		)
	}
	for row in rows:
		employee = info.get(row.employee, frappe._dict())
		row.tax_id = employee.thai_tax_id
		row.address = " ".join((employee.current_address or employee.permanent_address or "").split())
	return rows


@frappe.whitelist()
def make_year_end_certificates(company: str, year: int) -> dict:
	"""Create (or leave as they are) each employee's year-end 50 ทวิ for ภ.ง.ด.1ก."""
	frappe.has_permission("Thai WHT Certificate", "create", throw=True)
	year = int(year)
	start, end = getdate(f"{year}-01-01"), getdate(f"{year}-12-31")

	created, skipped, missing_tax_id = [], [], []
	for row in salary_rows(company, start, end):
		if frappe.db.exists(
			"Thai WHT Certificate",
			{"employee": row.employee, "pnd_form": "ภ.ง.ด.1ก", "docstatus": ["<", 2], "posting_date": ["between", [start, end]]},
		):
			skipped.append(row.employee)
			continue
		if not row.tax_id:
			missing_tax_id.append(row.employee_name)
			continue
		certificate = frappe.get_doc(
			{
				"doctype": "Thai WHT Certificate",
				"company": company,
				"posting_date": end,
				"pnd_form": "ภ.ง.ด.1ก",
				"condition": CONDITIONS[0],
				"employee": row.employee,
				"payee_name": row.employee_name,
				"payee_tax_id": row.tax_id,
				"payee_branch": "00000",
				"payee_address": row.address,
				"social_security_fund": flt(row.social_security),
				"provident_fund": flt(row.provident_fund),
				"items": [
					{
						"income_category": "40(1)",
						"description": _("เงินเดือน ค่าจ้าง ปีภาษี {0}").format(year + 543),
						"paid_date": end,
						"amount": flt(row.income),
						"tax_amount": flt(row.tax),
					}
				],
			}
		)
		certificate.insert()
		created.append(certificate.name)
	return {"created": created, "skipped": skipped, "missing_tax_id": missing_tax_id}
