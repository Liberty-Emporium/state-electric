Access-Control-Allow-Origin: *
HTTP/1.0 200 OK
Server: SimpleHTTP/0.6 Python/3.11.15
Date: Sun, 21 Jun 2026 05:06:00 GMT
Content-type: application/octet-stream
Content-Length: 10592
Last-Modified: Sun, 21 Jun 2026 04:02:03 GMT

# State Electric - QuickBooks Replacement App
## Project Planning Document v0.3
### Prepared by: Kilo (Jay's AI Assistant) for Jay Alexander
### Date: June 19, 2025

---

## 🏢 Company Overview

**State Electric** — An electrical services corporation structured as an umbrella company with two distinct business lines:
- **Commercial Electrical** division
- **Residential Electrical** division

**States of Operation:** North Carolina (primary), South Carolina, Tennessee, Virginia

**Key constraint:** Employees must be kept SEPARATE between commercial and residential divisions.

**Business Model:** One-time purchase fee. No subscriptions. No recurring charges. If app breaks, Jay fixes it (rare). Fair small-town pricing.

---

## 💰 Pricing Tiers — Revised

| Tier | Price | What They Get |
|------|-------|--------------|
| **Baseline** | **$1,500** | Everything an electrical company NEEDS to run: invoicing, customers, employees (20/div), basic reports, offline PWA |
| **Standard** | **$2,500** | Baseline + payroll engine, time tracking, job management, estimates, PDF generation |
| **Premium** | **$4,000** | Standard + AI estimates, advanced analytics, tax form generation (W-2, 941, 1099), API integrations |

**Why these prices:**
- QuickBooks costs $90-$200/MONTH = $1,080-$2,400 YEAR. Every year. Forever.
- Our app: pay once, own it forever. Even Premium pays for itself in year one.
- These are fair small-town prices for fair small-town people.
- Jay's profit margin is still healthy at these rates.

**Comparison:**
- QuickBooks Online Payroll: ~$1,500-$3,000/year (recurring, every year)
- Our Standard tier: $2,500 ONE TIME
- In 3 years, QuickBooks costs $4,500-$9,000. Our app still costs $2,500.

---

## 🆓 Add-On Features (After Initial Build)

If they want to add features later:
| Add-On | Price |
|--------|-------|
| AI estimates (if not Premium) | +$500 |
| Subcontractor 1099 module | +$300 |
| Additional state tax support (beyond NC, SC, TN, VA) | +$200 each |
| Custom invoice branding/design | +$300 |
| Bank import integration | +$500 |
| Multi-company support | +$750 |

---

## 📱 Offline-First Mobile Architecture (Critical Requirement)

Field technicians often have no internet at job sites. The app MUST work offline.

### How It Works:
1. **Local Storage** — Data is stored in the browser using IndexedDB
2. **Service Worker** — Caches the entire app shell (like a native app)
3. **Sync Queue** — Changes made offline are queued locally
4. **Auto-Sync** — When connection is restored, queued data auto-uploads to the server
5. **Conflict Resolution** — Last-write-wins with timestamps (simple, effective)

### Tech for Offline:
- **PWA (Progressive Web App)** — Installs on phone home screen, works like native app
- **Workbox** — Google's service worker library for caching
- **IndexedDB via Dexie.js** — Client-side database in the browser
- **Custom sync engine** — Django REST API endpoint that accepts batched updates

---

## 📋 Feature Breakdown by Tier

### 🟢 BASELINE ($1,500)

#### User & Employee Management
- Owner/Admin login
- Add up to 20 employees per division (40 total)
- Assign employees to Commercial OR Residential division
- Employee profiles: name, role, pay rate, contact info, hire date
- Role-based access: Owner, Manager, Employee

#### Customer Management
- Add/edit/delete customers
- Customer profile: name, company, address, phone, email, notes
- Tag customers as Commercial or Residential
- Customer job history

#### Invoicing
- Create invoices from scratch
- Line items: description, quantity, rate, amount
- Tax calculation (per-state rates for NC, SC, TN, VA)
- Invoice status: Draft → Sent → Paid → Overdue
- PDF invoice generation (printable/professional)
- Payment recording (check, cash, card, ACH)

#### Basic Reporting
- Revenue by division (commercial vs residential)
- Outstanding invoices / accounts receivable
- Monthly revenue summary

#### Offline Support (PWA)
- Full app works offline
- Create invoices offline
- Add customers offline
- Auto-sync when back online
- Install on phone home screen

---

### 🟡 STANDARD ($2,500) — Everything in Baseline, plus:

#### Payroll Engine
- Pay periods (weekly, bi-weekly, semi-monthly, monthly)
- Hours entry per employee per pay period
- Gross pay calculation (hours × rate)
- Overtime calculation (1.5× after 40 hrs/week — NC law)
- Federal tax withholding (based on W-4, IRS Publication 15-T)
- State tax withholding (NC, SC, VA — TN has no income tax)
- FICA (Social Security 6.2%, Medicare 1.45%)
- Net pay calculation
- Pay stub generation (PDF)
- Year-to-date totals per employee

#### Time Tracking
- Clock in / clock out
- Assign time to specific jobs
- Track hours by division
- Timesheet view per employee per pay period
- Offline time tracking (syncs when back online)

#### Job Management
- Create jobs (commercial or residential)
- Assign employees to jobs
- Job status: Scheduled → In Progress → Completed → Invoiced
- Job notes and descriptions
- Link invoices to jobs

#### Estimates/Quotes
- Create professional estimates
- Convert estimate to invoice (one click)
- Estimate templates for common electrical work
- PDF estimate generation

#### Enhanced Reports
- Payroll summary by pay period
- Job profitability (revenue vs labor cost)
- Employee hours report
- Customer billing history
- Quarterly tax summary

---

### 🔴 PREMIUM ($4,000) — Everything in Standard, plus:

#### AI-Powered Estimates (Local Ollama — No API Fees)
- AI suggests line items based on job description
- "Panel upgrade 200A residential" → auto-generates materials + labor
- Learns from historical jobs to improve suggestions
- Runs on local Ollama model (zero API costs, completely private)

#### Advanced Analytics Dashboard
- Revenue trends (monthly, quarterly, year-over-year)
- Division comparison (commercial vs residential profitability)
- Employee productivity metrics
- Top customers by revenue
- Cash flow forecasting

#### Tax Form Generation
- W-2 generation for employees (all states)
- 1099-NEC generation for subcontractors
- IRS Form 941 (quarterly federal tax return)
- State quarterly tax forms (NC, SC, VA — TN none)
- Year-end tax package export

#### Subcontractor (1099) Management
- Track subcontractor payments
- 1099-NEC generation
- Separate from W-2 employees

#### API & Integrations
- Bank transaction import (CSV/QBO)
- Email integration (send invoices via email)
- Calendar integration for scheduling
- Export data to CSV/Excel

---

## 🏗️ Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Backend** | Python 3.12 + Django 5.x | Jay's stack, rapid dev, batteries included |
| **API** | Django REST Framework | Clean API for PWA frontend + sync engine |
| **Frontend** | Django Templates + HTMX + Alpine.js | Fast, simple, no SPA complexity |
| **PWA** | Workbox + Dexie.js | Offline-first, service worker, IndexedDB |
| **Database** | PostgreSQL 16 | Robust, free, great with Django |
| **Auth** | Django built-in | Roles, permissions, session management |
| **PDF** | WeasyPrint | Professional PDF invoices, estimates, pay stubs |
| **AI (Premium)** | Ollama (local, offline) | Zero API costs, runs on server, learns from data |
| **Deployment** | VPS (Ubuntu) | Full control, minimal cost |
| **SSL** | Let's Encrypt | Free HTTPS |

---

## 🔐 Employee Separation Architecture

```
State Electric Corp (Django App)
│
├── Commercial Division (Group: commercial)
│   ├── Employees (max 20)
│   ├── Customers (tagged commercial)
│   ├── Jobs (commercial)
│   ├── Invoices (commercial)
│   ├── Time Entries (commercial)
│   └── Reports (commercial only)
│
├── Residential Division (Group: residential)
│   ├── Employees (max 20)
│   ├── Customers (tagged residential)
│   ├── Jobs (residential)
│   ├── Invoices (residential)
│   ├── Time Entries (residential)
│   └── Reports (residential only)
│
└── Owner/Admin (superuser — sees ALL)
```

**Enforcement:** Django permissions + queryset filtering. Employees only see their division's data. Owners see everything.

---

## 📅 Development Timeline

| Phase | Scope | Duration |
|-------|-------|----------|
| **Phase 1** | Foundation: models, auth, admin, PWA shell | Week 1-2 |
| **Phase 2** | Baseline features: customers, invoicing, basic reports | Week 3-4 |
| **Phase 3** | Offline sync engine + PWA polish | Week 5 |
| **Phase 4** | Standard features: payroll, time tracking, jobs, estimates | Week 6-7 |
| **Phase 5** | Standard reports + PDF generation | Week 8 |
| **Phase 6** | Premium features: AI estimates, analytics, tax forms | Week 9-11 |
| **Phase 7** | Testing, UAT with customer, bug fixes | Week 12 |
| **Phase 8** | Go live + QuickBooks data migration if needed | Week 13 |

**Baseline delivery: ~5 weeks**
**Standard delivery: ~8 weeks**
**Premium delivery: ~13 weeks**

---

## ⚠️ Key Technical Decisions

### Offline-First is Non-Negotiable
This is the hardest technical challenge. The sync engine must handle:
- Creating records offline (temporary local IDs → server IDs on sync)
- Editing records that were created offline
- Conflict resolution (two people edit same record offline)
- Reliable sync queue (retry on failure)

### Payroll Tax Accuracy
- IRS Publication 15-T for federal withholding
- State tax tables for NC, SC, VA (TN = no state income tax)
- Update tax tables annually
- Overtime: 1.5× after 40 hrs/week (federal + NC law)

### One-Time Fee = Self-Hosted, Zero Recurring Costs
- Self-hosted on customer's VPS or Jay-managed server
- No paid third-party APIs
- AI uses local Ollama (no API costs)
- Jay charges separately for fixes/support as needed (rare)

---

## ❓ Remaining Questions for Customer

1. Do they have a server/VPS, or should Jay host/manage it?
2. Do they use subcontractors (1099) or only W-2 employees?
3. What's their current process for tracking time? (paper, spreadsheet, QuickBooks?)
4. Do they need progress billing or only final invoices?
5. Do they have recurring/service contract customers?
6. How do they currently handle payroll?
7. Any specific invoice branding requirements?

---

## 📝 Rules of Engagement

1. **NO CODE until plan is reviewed and approved by Jay**
2. Customer conversation will refine requirements
3. After customer meeting, review plan together
4. Lock scope → then build
5. One-time fee model — keep everything free/open-source for customer
