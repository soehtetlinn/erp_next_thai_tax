"""Printable ภ.ง.ด.1, ภ.ง.ด.1ก, ภ.ง.ด.3 and ภ.ง.ด.53: the main form (portrait) followed by the
attachment sheets (ใบแนบ, landscape), in the layout of the Revenue Department's paper forms.

The figures come from the same reports used on screen (Thai PND Attachment, Thai PND 1 and
Thai PND 1 Kor), so the printout always matches them.
"""

from io import BytesIO

import frappe
from frappe import _
from frappe.utils import flt, nowdate
from frappe.utils.pdf import get_pdf

from thai_tax.utils import company_address, thai_month

FORMS = {
	"PND3": {
		"code": "ภ.ง.ด.3",
		"title": "แบบยื่นรายการภาษีเงินได้หัก ณ ที่จ่าย",
		"law": "ตามมาตรา 3 เตรส แห่งประมวลรัษฎากร",
		"payees": "บุคคลธรรมดา",
		"rows_per_sheet": 6,
	},
	"PND53": {
		"code": "ภ.ง.ด.53",
		"title": "แบบยื่นรายการภาษีเงินได้หัก ณ ที่จ่าย",
		"law": "ตามมาตรา 3 เตรส และมาตรา 69 ทวิ และการเสียภาษีตามมาตรา 65 จัตวา แห่งประมวลรัษฎากร",
		"payees": "นิติบุคคล",
		"rows_per_sheet": 6,
	},
	"PND1": {
		"code": "ภ.ง.ด.1",
		"title": "แบบยื่นรายการภาษีเงินได้หัก ณ ที่จ่าย",
		"law": "ตามมาตรา 59 แห่งประมวลรัษฎากร",
		"payees": "ผู้มีเงินได้ตามมาตรา 40 (1) (2)",
		"rows_per_sheet": 8,
	},
	"PND1K": {
		"code": "ภ.ง.ด.1ก",
		"title": "แบบแสดงรายการภาษีเงินได้หัก ณ ที่จ่าย",
		"law": "ตามมาตรา 58 (2) ซึ่งได้จ่ายเงินได้พึงประเมินตามมาตรา 40 (1) (2) แห่งประมวลรัษฎากร",
		"payees": "ผู้มีเงินได้ตามมาตรา 40 (1) (2)",
		"rows_per_sheet": 8,
	},
}


@frappe.whitelist()
def download(form: str, company: str, year: int, month: int | None = None, additional: int = 0):
	"""Download the form as PDF. additional > 0 prints it as ยื่นเพิ่มเติมครั้งที่ n."""
	if form not in FORMS:
		frappe.throw(_("Unknown form {0}").format(form))
	frappe.has_permission("Company", "read", company, throw=True)

	context = build_context(form, company, int(year), int(month) if month else None, int(additional or 0))
	main = get_pdf(frappe.render_template("thai_tax/templates/pnd/main.html", context), {"orientation": "Portrait"})
	sheets = get_pdf(frappe.render_template("thai_tax/templates/pnd/attachment.html", context), {"orientation": "Landscape"})

	# ASCII file name: Thai characters are garbled in the download header by some browsers
	frappe.local.response.filename = f"{form}-{context['period_key']}.pdf"
	frappe.local.response.filecontent = _merge(main, sheets)
	frappe.local.response.type = "pdf"


def build_context(form: str, company: str, year: int, month: int | None, additional: int) -> dict:
	spec = FORMS[form]
	lines, payees = _rows(form, company, year, month)

	size = spec["rows_per_sheet"]
	sheets = []
	for chunk in [payees[i : i + size] for i in range(0, len(payees), size)] or [[]]:
		chunk_lines = [line for payee in chunk for line in payee["lines"]]
		sheets.append(
			{
				"payees": chunk,
				"blank_rows": size - len(chunk),
				"amount": sum(flt(l["amount"]) for l in chunk_lines),
				"tax": sum(flt(l["tax"]) for l in chunk_lines),
			}
		)

	values = frappe.db.get_value("Company", company, ["tax_id", "thai_branch_code", "phone_no"], as_dict=True)
	total_amount = sum(flt(l["amount"]) for l in lines)
	total_tax = sum(flt(l["tax"]) for l in lines)
	return {
		"spec": spec,
		"form": form,
		"company": company,
		"company_tax_id": values.tax_id or "",
		"company_branch": values.thai_branch_code or "00000",
		"company_phone": values.phone_no or "",
		"company_address": company_address(company),
		"year_be": year + 543,
		"month": month,
		"month_name": thai_month(month) if month else "",
		"period_key": f"{year}-{month:02d}" if month else str(year),
		"additional": additional,
		"payees": payees,
		"sheets": sheets,
		"payee_count": len(payees),
		"total_amount": total_amount,
		"total_tax": total_tax,
		"filed_on": nowdate(),
	}


def _rows(form: str, company: str, year: int, month: int | None):
	"""Lines (one per income item) and payees (each with its lines), numbered as on the report."""
	if form in ("PND3", "PND53"):
		from thai_tax.thai_tax.report.thai_pnd_attachment.thai_pnd_attachment import execute

		_, rows, *__ = execute({"company": company, "pnd_form": FORMS[form]["code"], "month": month, "year": year})
		payees: dict = {}
		for r in rows:
			payee = payees.setdefault(
				r.certificate,
				{"sequence": r.sequence, "tax_id": r.payee_tax_id, "branch": r.payee_branch, "name": r.payee_name,
				 "address": r.payee_address, "lines": []},
			)
			payee["lines"].append(
				{"date": r.paid_date_th, "income": r.income, "rate": r.rate, "amount": r.amount, "tax": r.tax_amount,
				 "condition": r.condition_code}
			)
		payees = list(payees.values())
	else:
		if form == "PND1":
			from thai_tax.thai_tax.report.thai_pnd_1.thai_pnd_1 import execute

			_, rows, *__ = execute({"company": company, "month": month, "year": year})
		else:
			from thai_tax.thai_tax.report.thai_pnd_1_kor.thai_pnd_1_kor import execute

			_, rows, *__ = execute({"company": company, "year": year})
		payees = [
			{"sequence": r.sequence, "tax_id": r.tax_id or "", "branch": "", "name": r.employee_name,
			 "address": r.get("address") or "",
			 "lines": [{"date": r.get("paid_date_th") or "", "income": "40(1)", "rate": None, "amount": r.income,
			            "tax": r.tax, "condition": r.condition_code}]}
			for r in rows
		]
	lines = [line for payee in payees for line in payee["lines"]]
	return lines, payees


def _merge(*pdfs: bytes) -> bytes:
	from pypdf import PdfReader, PdfWriter

	writer = PdfWriter()
	for data in pdfs:
		for page in PdfReader(BytesIO(data)).pages:
			writer.add_page(page)
	out = BytesIO()
	writer.write(out)
	return out.getvalue()
