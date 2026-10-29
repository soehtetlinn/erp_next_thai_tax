"""Create 50 Tawi certificates from the withholding ERPNext records on purchases and payments.

ERPNext v16 keeps each withholding in the document's Tax Withholding Entries table. When a
Purchase Invoice or Payment Entry that withholds tax is submitted, one certificate is created
per supplier, with a row per withholding category; cancelling the document cancels it.
"""

import frappe
from frappe.contacts.doctype.address.address import get_address_display
from frappe.utils import flt

from thai_tax.constants import CONDITIONS, PND_FOR_INDIVIDUAL, PND_FOR_JURISTIC

CERTIFICATE = "Thai WHT Certificate"


def on_submit(doc, method=None):
	if frappe.get_cached_value("Company", doc.company, "country") != "Thailand":
		return

	by_supplier: dict[str, list] = {}
	for row in doc.get("tax_withholding_entries") or []:
		withheld_here = row.withholding_doctype == doc.doctype and row.withholding_name == doc.name
		if withheld_here and row.party_type == "Supplier" and flt(row.withholding_amount) > 0:
			by_supplier.setdefault(row.party, []).append(row)

	for supplier, rows in by_supplier.items():
		make_certificate(doc, supplier, rows).submit()


def on_cancel(doc, method=None):
	for name in frappe.get_all(
		CERTIFICATE,
		filters={"reference_doctype": doc.doctype, "reference_name": doc.name, "docstatus": 1},
		pluck="name",
	):
		frappe.get_doc(CERTIFICATE, name).cancel()


def make_certificate(doc, supplier: str, rows: list):
	info = frappe.db.get_value(
		"Supplier",
		supplier,
		["supplier_name", "supplier_type", "tax_id", "thai_branch_code", "supplier_primary_address"],
		as_dict=True,
	)
	address = doc.get("supplier_address") or info.supplier_primary_address
	certificate = frappe.get_doc(
		{
			"doctype": CERTIFICATE,
			"company": doc.company,
			"posting_date": doc.posting_date,
			"pnd_form": PND_FOR_INDIVIDUAL if info.supplier_type == "Individual" else PND_FOR_JURISTIC,
			"condition": CONDITIONS[0],
			"supplier": supplier,
			"payee_name": info.supplier_name,
			"payee_tax_id": info.tax_id or rows[0].tax_id,
			"payee_branch": info.thai_branch_code,
			"payee_address": get_address_display(address) if address else "",
			"reference_doctype": doc.doctype,
			"reference_name": doc.name,
		}
	)
	for row in rows:
		category = frappe.get_cached_value(
			"Tax Withholding Category",
			row.tax_withholding_category,
			["thai_income_category", "thai_income_description"],
			as_dict=True,
		)
		certificate.append(
			"items",
			{
				"income_category": category.thai_income_category or "3 เตรส",
				"description": category.thai_income_description or row.tax_withholding_category,
				"paid_date": row.withholding_date or doc.posting_date,
				"rate": row.tax_rate,
				"amount": row.taxable_amount,
				"tax_amount": row.withholding_amount,
			},
		)
	certificate.insert(ignore_permissions=True)
	return certificate
