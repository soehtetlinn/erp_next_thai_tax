### Thai Tax

Thai tax documents for ERPNext v16: full tax invoice, withholding tax certificates (50 ทวิ) and
the monthly ภ.ง.ด.3 / ภ.ง.ด.53 attachment.

```bash
bench get-app <repo-url> --branch version-16
bench --site <site> install-app thai_tax
```

#### What it adds

| Feature | Where |
|---|---|
| **Branch code** (สำนักงานใหญ่ = 00000 / สาขาที่) on Company, Customer and Supplier | the Tax ID section of each |
| **Thai Tax Invoice** print format: ใบกำกับภาษี with seller/buyer tax ID and branch, VAT, amount in Thai words, Buddhist Era dates | Sales Invoice → Print |
| **Withholding categories** for common payments: services, hire of work and professional fees 3%, rent 5%, advertising 2%, transport 1%, commission 3% (base excludes VAT, 1,000 baht threshold), and the account ภาษีเงินได้หัก ณ ที่จ่ายค้างจ่าย | Tax Withholding Category |
| **Thai WHT Certificate** (50 ทวิ), created automatically when a Purchase Invoice or Payment Entry that withholds tax is submitted, and cancelled with it. ภ.ง.ด.3 for suppliers of type Individual, ภ.ง.ด.53 otherwise | Thai WHT Certificate |
| **50 Tawi** print format: two copies (ฉบับที่ 1 for the payee's return, ฉบับที่ 2 for their records), per Director-General Announcement No. 100 | Thai WHT Certificate → Print |
| **Thai PND Attachment** report: ใบแนบ ภ.ง.ด.3 / ภ.ง.ด.53 for a month, with totals to remit; export to Excel for RD Prep / e-Filing | Reports |
| **Thai PND 1** report: ใบแนบ ภ.ง.ด.1, salary income (มาตรา 40 (1)) and tax for a month, from submitted Salary Slips | Reports |
| **Thai PND 1 Kor** report: ใบแนบ ภ.ง.ด.1ก, each employee's income, tax, social security and provident fund for the year, with a **Create Employee 50 Tawi** button that makes each employee's year-end certificate (as drafts, run again safely) | Reports |
| **Print Official Form** button on the three reports: the main ภ.ง.ด.3 / ภ.ง.ด.53 / ภ.ง.ด.1 / ภ.ง.ด.1ก form (portrait) with its attachment sheets (ใบแนบ, landscape, numbered "แผ่นที่ x ในจำนวน y"), as one PDF | Reports |
| **Thai Tax ID** on Employee and **Thai Fund Type** (Social Security / Provident Fund) on salary deduction components | Employee, Salary Component |

Thai text in PDFs uses the bundled **Sarabun** font (SIL Open Font License, `public/fonts/OFL.txt`),
so the server needs no Thai fonts installed. The PDF engine loads it from the site URL, so the
site's `host_name` must be reachable from the server itself.

#### Setting up

1. Company: Tax ID and branch code; a company address (shown on invoices and 50 ทวิ).
2. Suppliers you withhold from: Tax ID (13 digits), branch code, **Supplier Type** (Individual →
   ภ.ง.ด.3), and their **Tax Withholding Category**.
3. Purchase Invoice or Payment Entry: tick **Apply Tax Withholding Amount**. Submitting it creates
   the 50 ทวิ.
4. Each month (due the 7th, or the 15th when filed online): run **Thai PND Attachment** for
   ภ.ง.ด.3 and ภ.ง.ด.53, and **Thai PND 1** for salaries, for the previous month and file the totals.
5. Payroll: give every employee a **Thai Tax ID**, tick **Is Income Tax Component** on the income
   tax deduction, and set **Thai Fund Type** on the social security and provident fund deductions.
6. By the end of February: run **Thai PND 1 Kor** for last year, file it, then press
   **Create Employee 50 Tawi**, check and submit the drafts, and give each employee their copy.

Salary income is the gross pay of submitted Salary Slips, dated by each slip's posting date.

#### Not covered yet

- The RD Prep / e-Filing import file format (the reports export to Excel)
- ภ.พ.30 (monthly VAT return) and the input/output VAT reports

Rates, thresholds and layouts follow Revenue Department rules as researched in October 2026
(order ท.ป.4/2528, Announcement No. 100, Revenue Code sections 50 ทวิ and 86/4). Have your
accountant review them before filing.

#### License

mit
