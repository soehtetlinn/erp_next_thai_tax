# Copyright (c) 2026, Cactus Tree Co.,Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class ThaiWHTCertificate(Document):
	"""หนังสือรับรองการหักภาษี ณ ที่จ่าย ตามมาตรา 50 ทวิ (50 Tawi)."""

	def validate(self):
		self.payee_tax_id = "".join(c for c in (self.payee_tax_id or "") if c.isdigit())
		if len(self.payee_tax_id) != 13:
			frappe.throw(_("The payee's tax ID must have 13 digits."))

		self.payee_branch = (self.payee_branch or "00000").strip()
		if not (self.payee_branch.isdigit() and len(self.payee_branch) == 5):
			frappe.throw(_("The branch code must have 5 digits (00000 for head office)."))

		for row in self.items:
			if flt(row.tax_amount) < 0 or flt(row.amount) <= 0:
				frappe.throw(_("Row {0}: the amount paid must be positive.").format(row.idx))

		self.total_amount = sum(flt(row.amount) for row in self.items)
		self.total_tax = sum(flt(row.tax_amount) for row in self.items)
