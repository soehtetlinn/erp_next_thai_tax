"""Thai withholding tax reference data."""

PND_FORMS = ["ภ.ง.ด.1ก", "ภ.ง.ด.1ก พิเศษ", "ภ.ง.ด.2", "ภ.ง.ด.3", "ภ.ง.ด.2ก", "ภ.ง.ด.3ก", "ภ.ง.ด.53"]

# Payments to individuals are filed on ภ.ง.ด.3, payments to companies and partnerships on ภ.ง.ด.53
PND_FOR_INDIVIDUAL = "ภ.ง.ด.3"
PND_FOR_JURISTIC = "ภ.ง.ด.53"

CONDITIONS = ["1. หัก ณ ที่จ่าย", "2. ออกให้ตลอดไป", "3. ออกให้ครั้งเดียว", "4. อื่น ๆ"]

# Rows of the income table on the 50 Tawi certificate, by the Revenue Code section they fall under
INCOME_CATEGORIES = {
	"40(1)": "1. เงินเดือน ค่าจ้าง เบี้ยเลี้ยง โบนัส ฯลฯ ตามมาตรา 40 (1)",
	"40(2)": "2. ค่าธรรมเนียม ค่านายหน้า ฯลฯ ตามมาตรา 40 (2)",
	"40(3)": "3. ค่าแห่งลิขสิทธิ์ ฯลฯ ตามมาตรา 40 (3)",
	"40(4)(ก)": "4. (ก) ดอกเบี้ย ฯลฯ ตามมาตรา 40 (4) (ก)",
	"40(4)(ข)": "4. (ข) เงินปันผล เงินส่วนแบ่งกำไร ฯลฯ ตามมาตรา 40 (4) (ข)",
	"3 เตรส": "5. การจ่ายเงินได้ที่ต้องหักภาษี ณ ที่จ่าย ตามคำสั่งกรมสรรพากรที่ออกตามมาตรา 3 เตรส",
	"อื่น ๆ": "6. อื่น ๆ",
}

# Common withholding categories created for each Thai company. Rates per Revenue Department
# order ท.ป.4/2528; the base is the amount before VAT. Check with your accountant.
DEFAULT_CATEGORIES = [
	# (name, rate, income category, description on the certificate)
	("TH WHT Services 3%", 3, "3 เตรส", "ค่าบริการ"),
	("TH WHT Hire of Work 3%", 3, "3 เตรส", "ค่าจ้างทำของ"),
	("TH WHT Professional Fees 3%", 3, "3 เตรส", "ค่าวิชาชีพอิสระ"),
	("TH WHT Rent 5%", 5, "3 เตรส", "ค่าเช่า"),
	("TH WHT Advertising 2%", 2, "3 เตรส", "ค่าโฆษณา"),
	("TH WHT Transport 1%", 1, "3 เตรส", "ค่าขนส่ง"),
	("TH WHT Commission 3%", 3, "40(2)", "ค่านายหน้า"),
]

WHT_ACCOUNT_NAME = "ภาษีเงินได้หัก ณ ที่จ่ายค้างจ่าย"
