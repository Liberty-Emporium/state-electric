Access-Control-Allow-Origin: *
HTTP/1.0 200 OK
Server: SimpleHTTP/0.6 Python/3.11.15
Date: Sun, 21 Jun 2026 05:06:00 GMT
Content-type: application/octet-stream
Content-Length: 6797
Last-Modified: Sun, 21 Jun 2026 04:02:03 GMT

# STATE ELECTRIC — FULL PROJECT PACKAGE
## QuickBooks Replacement App for Electrical Contractor
### Prepared by Kilo (Jay's AI assistant on Beast)
### Date: June 19, 2025
### FOR: Another agent to build on Linux

---

## 📌 WHAT IS THIS?

State Electric is an electrical services corporation that wants to replace QuickBooks with a custom web app. Jay (the developer, owner of Alexander AI Solutions) has already:
- Talked to the customer (John and Rhonda at State Electric)
- Agreed on pricing and features
- Sent the customer an audio pitch (customer approved)
- Written a contract (ready to sign)

**Jay wants YOU to build the Essential tier first, get it deployed so the customer can see it, THEN they sign the contract and you continue with Standard features.**

---

## 🏢 COMPANY INFO

- **Company:** State Electric (electrical services corporation)
- **Structure:** Umbrella company with TWO divisions that must stay SEPARATE
  - Commercial Electrical
  - Residential Electrical
- **States:** NC (primary), SC, TN, VA
- **Employees:** Up to 20 per division (40 total)
- **Current software:** QuickBooks (they're migrating FROM QuickBooks TO this app)

---

## 💰 PRICING (REVISED — ALL-IN PACKAGE)

| Package | Price | Status |
|---------|-------|--------|
| **Complete** (Essential + Standard + Premium) | **$3,500** | **Build ALL** |

**Payment:** 50% upfront ($1,750), 50% on delivery ($1,750)

**Why one package:** Customer needs a full QuickBooks replacement. Selling piecemeal creates friction and risks losing the sale. One price, everything included.

---

## 📋 BUILD ORDER

### PHASE 1: Essential (DONE ✅)
Customer management, employee management, invoicing, basic reports, offline PWA

### PHASE 2: Standard (DONE ✅)
Payroll, time tracking, job management, estimates, PDF generation, reports

### PHASE 3: Premium (BUILD NOW)
Recurring invoices, expense tracking, bank reconciliation, purchase orders, 1099 support, AI estimates, tax forms, data import, contracts

---

## 🏗️ TECH STACK

- **Backend:** Python 3.12 + Django 5.x
- **API:** Django REST Framework
- **Frontend:** Django Templates + HTMX + Alpine.js
- **PWA:** Workbox service worker + Dexie.js (IndexedDB) for offline
- **Database:** PostgreSQL
- **PDF:** WeasyPrint
- **Deployment:** Ubuntu VPS or Railway
- **SSL:** Let's Encrypt

---

## 📱 OFFLINE-FIRST REQUIREMENT (CRITICAL)

Field techs have NO internet at job sites. The app MUST:
1. Work fully offline (Service Worker caches the app shell)
2. Store data locally in IndexedDB via Dexie.js
3. Queue all changes made offline
4. Auto-sync when connection returns
5. Handle conflicts (last-write-wins)

This is the HARDEST part of the build. Don't skip it.

---

## 🔐 EMPLOYEE SEPARATION

Commercial and residential employees MUST NOT see each other's data.
- Each employee is assigned to ONE division
- Django Groups enforce separation: `commercial` and `residential` groups
- All querysets filtered by division
- Owner/Admin (superuser) sees EVERYTHING

---

## 📋 ESSENTIAL TIER FEATURES (BUILD FIRST)

### Models needed:
1. **User** (extend Django's AbstractUser)
2. **Division** (Commercial, Residential)
3. **Employee** (linked to User + Division)
4. **Customer** (name, company, address, phone, email, notes, division)
5. **Invoice** (customer, number, date, due_date, status, tax_rate, notes)
6. **InvoiceLineItem** (invoice, description, quantity, rate, amount)
7. **Payment** (invoice, amount, date, method, reference)

### Views needed:
- Login / Logout
- Dashboard (revenue summary, outstanding invoices)
- Customer list / detail / create / edit / delete
- Invoice list / detail / create / edit / send / mark paid
- Employee list / create / edit (admin only)
- Basic reports (revenue by division, outstanding AR)

### UI:
- Mobile-first responsive design
- Install as PWA (add to home screen)
- Works offline (service worker + IndexedDB sync)
- Clean, professional look (Bootstrap 5 or similar)

### URLs:
- `/accounts/login/`
- `/dashboard/`
- `/customers/`
- `/invoices/`
- `/employees/`
- `/reports/`

---

## 📋 STANDARD TIER FEATURES (AFTER CONTRACT)

Add these after Essential is deployed and contract is signed:

### Additional Models:
8. **Job** (title, customer, division, description, status, scheduled_date)
9. **TimeEntry** (employee, job, date, hours, description)
10. **PayPeriod** (start_date, end_date, division)
11. **PayrollEntry** (pay_period, employee, regular_hours, overtime_hours, gross_pay, federal_tax, state_tax, fica, net_pay)
12. **Estimate** (customer, division, date, status, total)
13. **EstimateLineItem** (estimate, description, quantity, rate, amount)

### Tax calculations:
- Federal: IRS Publication 15-T tables
- NC state tax
- SC state tax
- VA state tax
- TN: NO state income tax
- Overtime: 1.5x after 40 hrs/week
- FICA: SS 6.2%, Medicare 1.45%

### Pay stub PDF generation
### Time tracking (clock in/out)
### Job workflow: Scheduled → In Progress → Completed → Invoiced
### Estimate → Invoice conversion

---

## 📋 QUICKBOOKS DATA MIGRATION

After building, you'll need to migrate their QuickBooks data:
- Customers → Customer model
- Employees → Employee + User models
- Invoices → Invoice + InvoiceLineItem models
- Payment history → Payment model

Build a management command: `python manage.py migrate_quickbooks <file_or_api>`

---

## 📄 CONTRACT SUMMARY

Full contract at: (Jay has the signed copy)

Key points:
- 50/50 payment ($1,750 now, $1,750 on delivery)
- 90-day bug fix warranty
- Jay not responsible for taxes, bookkeeping, hardware, data loss
- Client responsible for QuickBooks data export, timely feedback, own backups
- Hosting: self-hosted free, or managed at $75/year

---

## 📞 CUSTOMER CONTACT

The customer is John and Rhonda Tig at State Electric.
Jay has been communicating with them via text/audio messages.
All feature decisions have been approved by both Jay and John/Rhonda.

---

## ⚠️ IMPORTANT RULES

1. **Build Essential FIRST, deploy it, let customer review**
2. **Do NOT start Standard until contract is signed**
3. **Offline-first is NON-NEGOTIABLE** — field techs have no signal at job sites
4. **Employee separation is NON-NEGOTIABLE** — commercial/residential must be isolated
5. **Keep all costs free/open-source** — no paid API dependencies
6. **Mobile-first design** — most users will be on phones at job sites
7. **NC, SC, TN, VA tax support** from day one

---

## 🎯 SUCCESS CRITERIA

- Customer can create and send invoices from their phone
- Employees can clock in/out from their phone at job sites (offline)
- Commercial and residential data is completely separate
- Dashboard shows revenue by division
- Works on iPhone and Android (PWA)
- Looks professional enough for a business to rely on
- QuickBooks data imports without data loss

Good luck! Jay is counting on you. 🤝
