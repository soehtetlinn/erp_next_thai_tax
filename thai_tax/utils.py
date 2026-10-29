"""Thai formatting helpers, available in print formats (see jinja in hooks.py)."""

from frappe.utils import flt, getdate

_DIGITS = ["", "หนึ่ง", "สอง", "สาม", "สี่", "ห้า", "หก", "เจ็ด", "แปด", "เก้า"]
_UNITS = ["", "สิบ", "ร้อย", "พัน", "หมื่น", "แสน"]
_MONTHS = [
	"มกราคม",
	"กุมภาพันธ์",
	"มีนาคม",
	"เมษายน",
	"พฤษภาคม",
	"มิถุนายน",
	"กรกฎาคม",
	"สิงหาคม",
	"กันยายน",
	"ตุลาคม",
	"พฤศจิกายน",
	"ธันวาคม",
]

HEAD_OFFICE = "00000"


def _read_number(number: int, has_higher_part: bool = False) -> str:
	"""Thai words for a whole number. A trailing 1 reads เอ็ด after tens or a higher part."""
	if number == 0:
		return ""
	if number >= 1_000_000:
		rest = number % 1_000_000
		return _read_number(number // 1_000_000) + "ล้าน" + _read_number(rest, has_higher_part=True)

	digits = str(number)
	words = ""
	for index, char in enumerate(digits):
		digit = int(char)
		position = len(digits) - index - 1
		if digit == 0:
			continue
		if position == 1 and digit == 1:
			words += "สิบ"
		elif position == 1 and digit == 2:
			words += "ยี่สิบ"
		elif position == 0 and digit == 1 and (len(digits) > 1 or has_higher_part):
			words += "เอ็ด"
		else:
			words += _DIGITS[digit] + _UNITS[position]
	return words


def bahttext(amount) -> str:
	"""Amount in Thai words, as written on tax invoices and 50 Tawi: 1250.50 -> หนึ่งพันสองร้อยห้าสิบบาทห้าสิบสตางค์"""
	amount = round(flt(amount), 2)
	sign = "ลบ" if amount < 0 else ""
	satang_total = round(abs(amount) * 100)
	baht, satang = divmod(satang_total, 100)
	if baht == 0 and satang == 0:
		return "ศูนย์บาทถ้วน"
	words = _read_number(baht) + "บาท" if baht else ""
	words += _read_number(satang) + "สตางค์" if satang else "ถ้วน"
	return sign + words


def thai_date(value, short: bool = False) -> str:
	"""29 ตุลาคม 2569 (Buddhist Era), or 29/10/2569 with short=True."""
	if not value:
		return ""
	date = getdate(value)
	if short:
		return f"{date.day:02d}/{date.month:02d}/{date.year + 543}"
	return f"{date.day} {_MONTHS[date.month - 1]} {date.year + 543}"


def thai_month(month: int) -> str:
	return _MONTHS[int(month) - 1]


def branch_label(code) -> str:
	"""How a branch is written on Thai tax documents."""
	code = (code or "").strip()
	if not code or code == HEAD_OFFICE:
		return "สำนักงานใหญ่"
	return f"สาขาที่ {code}"


def format_tax_id(tax_id) -> str:
	"""0105556012345 -> 0 1055 56012 34 5, the grouping used on Thai forms."""
	digits = "".join(c for c in (tax_id or "") if c.isdigit())
	if len(digits) != 13:
		return tax_id or ""
	return f"{digits[0]} {digits[1:5]} {digits[5:10]} {digits[10:12]} {digits[12]}"


def company_address(company: str) -> str:
	"""The company's main address as one line, for the issuer block on Thai documents."""
	from frappe.contacts.doctype.address.address import get_address_display, get_default_address

	address = get_default_address("Company", company)
	if not address:
		return ""
	return " ".join(line.strip() for line in get_address_display(address).replace("<br>", "\n").splitlines() if line.strip())


def font_css() -> str:
	"""@font-face rules for the Sarabun font bundled with this app (public/fonts), so PDFs show
	Thai on servers without Thai fonts installed. The PDF engine (wkhtmltopdf) fetches the font
	from the site, the same way it fetches Frappe's own stylesheets; it ignores fonts embedded
	in the CSS as data URIs. (A plain function: Frappe only exposes plain functions to print
	formats.)"""
	from frappe.utils import get_url

	base = f"{get_url()}/assets/thai_tax/fonts"
	return "\n".join(
		"@font-face { font-family: 'Sarabun'; font-weight: %d; src: url('%s/%s') format('truetype'); }"
		% (weight, base, filename)
		for weight, filename in ((400, "Sarabun-Regular.ttf"), (700, "Sarabun-Bold.ttf"))
	)
