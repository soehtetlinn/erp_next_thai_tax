import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields as _create

from thai_tax.constants import DEFAULT_CATEGORIES, INCOME_CATEGORIES, WHT_ACCOUNT_NAME

BRANCH_FIELD = {
	"fieldname": "thai_branch_code",
	"label": "Branch Code (Thai)",
	"fieldtype": "Data",
	"length": 5,
	"default": "00000",
	"insert_after": "tax_id",
	"description": "00000 = head office (สำนักงานใหญ่). Shown on Thai tax invoices and withholding forms.",
}


def after_install():
	create_custom_fields()
	add_to_accounts_sidebar()
	for company in frappe.get_all("Company", filters={"country": "Thailand"}, pluck="name"):
		setup_company(company)


def create_custom_fields():
	_create(
		{
			"Company": [BRANCH_FIELD],
			"Customer": [BRANCH_FIELD],
			"Supplier": [BRANCH_FIELD],
			"Employee": [
				{
					"fieldname": "thai_tax_id",
					"label": "Thai Tax ID (เลขประจำตัวผู้เสียภาษี)",
					"fieldtype": "Data",
					"length": 13,
					"insert_after": "passport_number",
					"description": "13-digit national ID number. Needed for ภ.ง.ด.1, ภ.ง.ด.1ก and the year-end 50 ทวิ.",
				}
			],
			"Salary Component": [
				{
					"fieldname": "thai_fund_type",
					"label": "Thai Fund Type",
					"fieldtype": "Select",
					"options": "\nSocial Security\nProvident Fund",
					"insert_after": "is_income_tax_component",
					"depends_on": "eval:doc.type == 'Deduction'",
					"description": "Totals of these deductions are printed on the employee's year-end 50 ทวิ. Mark the income tax deduction with Is Income Tax Component.",
				}
			],
			"Tax Withholding Category": [
				{
					"fieldname": "thai_income_category",
					"label": "Thai Income Type (50 Tawi row)",
					"fieldtype": "Select",
					"options": "\n" + "\n".join(INCOME_CATEGORIES),
					"insert_after": "category_name",
				},
				{
					"fieldname": "thai_income_description",
					"label": "Description on 50 Tawi",
					"fieldtype": "Data",
					"insert_after": "thai_income_category",
					"description": "For example ค่าบริการ, ค่าเช่า, ค่าโฆษณา",
				},
			],
		},
		update=True,
	)
	frappe.make_property_setter(
		{
			"doctype": "Thai WHT Certificate",
			"doctype_or_field": "DocType",
			"property": "default_print_format",
			"value": "50 Tawi",
			"property_type": "Data",
		},
		validate_fields_for_doctype=False,
	)


# Thai tax entries for ERPNext's Accounts sidebar: their own "Thai Tax" section, right below Taxes.
# (The v16 sidebar has one level of sections, so it cannot sit inside Taxes itself.)
SIDEBAR_SECTION = "Thai Tax"
SIDEBAR_ITEMS = [
	("ใบ 50 ทวิ (WHT Certificate)", "DocType", "Thai WHT Certificate"),
	("ภ.ง.ด.3 / ภ.ง.ด.53", "Report", "Thai PND Attachment"),
	("ภ.ง.ด.1", "Report", "Thai PND 1"),
	("ภ.ง.ด.1ก", "Report", "Thai PND 1 Kor"),
]


def after_migrate():
	create_custom_fields()
	add_to_accounts_sidebar()


def add_to_accounts_sidebar():
	"""Give the Thai tax forms a "Thai Tax" section in the Accounts sidebar, right below Taxes.

	The Accounts sidebar is ERPNext's own and is reloaded from its files on every update, so the
	section goes into the site's layer over it (a Custom Sidebar), the place Frappe keeps a site's
	changes to an app's sidebar. When the section is already in place nothing is written; Thai
	items found anywhere else (such as inside Taxes, where earlier versions put them) are moved.
	"""
	from frappe.desk.doctype.custom_sidebar.custom_sidebar import _save_customization, layer_arrangement

	if not frappe.db.exists("Module Def", "Accounts"):
		return
	rows = layer_arrangement("Accounts", None)
	ours = {link_to for _, _, link_to in SIDEBAR_ITEMS}

	def is_ours(row):
		is_section = row.get("type") == "Section Break" and row.get("label") == SIDEBAR_SECTION
		return is_section or row.get("link_to") in ours

	block = [
		{
			"added": 1,
			"type": "Section Break",
			"label": SIDEBAR_SECTION,
			"icon": "receipt",
			"collapsible": 1,
			"indent": 1,
			"keep_closed": 1,
		}
	] + [
		{"added": 1, "type": "Link", "label": label, "link_type": link_type, "link_to": link_to, "child": 1}
		for label, link_type, link_to in SIDEBAR_ITEMS
	]

	others = [row for row in rows if not is_ours(row)]
	# after the Taxes section and its entries, or at the end if this site has no Taxes section
	position = len(others)
	taxes = next((i for i, row in enumerate(others) if row.get("type") == "Section Break" and row.get("label") == "Taxes"), None)
	if taxes is not None:
		position = taxes + 1
		while position < len(others) and others[position].get("child") and others[position].get("type") != "Section Break":
			position += 1

	current = [(row.get("type"), row.get("label"), row.get("link_to")) for row in rows if is_ours(row)]
	wanted = [(row["type"], row["label"], row.get("link_to")) for row in block]
	in_place = current == wanted and rows[position : position + len(block)] and is_ours(rows[position])
	if in_place:
		return
	_save_customization("Accounts", others[:position] + block + others[position:], user=None)


def setup_company(company: str):
	"""Create the withholding tax payable account and the common Thai withholding categories."""
	account = _wht_account(company)
	for name, rate, income_category, description in DEFAULT_CATEGORIES:
		if frappe.db.exists("Tax Withholding Category", name):
			category = frappe.get_doc("Tax Withholding Category", name)
			if not any(row.company == company for row in category.accounts):
				category.append("accounts", {"company": company, "account": account})
				category.save(ignore_permissions=True)
			continue
		frappe.get_doc(
			{
				"doctype": "Tax Withholding Category",
				"name": name,
				"category_name": name,
				"thai_income_category": income_category,
				"thai_income_description": description,
				# Thai withholding is worked out on the amount before VAT
				"tax_deduction_basis": "Net Total",
				"rates": [
					{
						"from_date": "2020-01-01",
						"to_date": "2099-12-31",
						"tax_withholding_rate": rate,
						# withhold on payments of 1,000 baht or more
						"single_threshold": 1000,
						"cumulative_threshold": 0,
					}
				],
				"accounts": [{"company": company, "account": account}],
			}
		).insert(ignore_permissions=True)


def _wht_account(company: str) -> str:
	abbr = frappe.get_cached_value("Company", company, "abbr")
	name = f"{WHT_ACCOUNT_NAME} - {abbr}"
	if frappe.db.exists("Account", name):
		return name
	parent = frappe.db.get_value(
		"Account", {"company": company, "account_type": "Tax", "is_group": 1, "root_type": "Liability"}
	) or frappe.db.get_value("Account", {"company": company, "account_name": "Duties and Taxes", "is_group": 1})
	return (
		frappe.get_doc(
			{
				"doctype": "Account",
				"account_name": WHT_ACCOUNT_NAME,
				"company": company,
				"parent_account": parent,
				"account_type": "Tax",
				"root_type": "Liability",
			}
		)
		.insert(ignore_permissions=True)
		.name
	)
