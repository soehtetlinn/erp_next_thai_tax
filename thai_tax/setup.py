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
	for company in frappe.get_all("Company", filters={"country": "Thailand"}, pluck="name"):
		setup_company(company)


def create_custom_fields():
	_create(
		{
			"Company": [BRANCH_FIELD],
			"Customer": [BRANCH_FIELD],
			"Supplier": [BRANCH_FIELD],
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
