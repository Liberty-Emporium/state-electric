"""URL configuration for State Electric."""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

from core import views as core_views
from core.pwa_views import pwa_manifest, service_worker
from invoicing import views as inv_views
from reporting import views as report_views
from standard import views as std_views
from premium import views as prem_views

from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path('health/', health_check, name='health'),
    path('admin/', admin.site.urls),

    # Auth
    path('accounts/login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Dashboard
    path('dashboard/', core_views.dashboard, name='dashboard'),
    path('', core_views.dashboard, name='home'),

    # Customers
    path('customers/', include([
        path('', core_views.CustomerListView.as_view(), name='customer-list'),
        path('add/', core_views.CustomerCreateView.as_view(), name='customer-create'),
        path('<int:pk>/', core_views.CustomerDetailView.as_view(), name='customer-detail'),
        path('<int:pk>/edit/', core_views.CustomerUpdateView.as_view(), name='customer-edit'),
        path('<int:pk>/delete/', core_views.customer_delete, name='customer-delete'),
    ])),

    # Invoices
    path('invoices/', include([
        path('', inv_views.InvoiceListView.as_view(), name='invoice-list'),
        path('add/', inv_views.InvoiceCreateView.as_view(), name='invoice-create'),
        path('<int:pk>/', inv_views.InvoiceDetailView.as_view(), name='invoice-detail'),
        path('<int:pk>/edit/', inv_views.InvoiceUpdateView.as_view(), name='invoice-edit'),
        path('<int:pk>/payment/', inv_views.invoice_add_payment, name='invoice-add-payment'),
        path('<int:pk>/status/', inv_views.invoice_update_status, name='invoice-update-status'),
        path('<int:pk>/pdf/', inv_views.invoice_pdf, name='invoice-pdf'),
    ])),

    # Jobs (Standard tier)
    path('jobs/', include([
        path('', std_views.JobListView.as_view(), name='job-list'),
        path('add/', std_views.JobCreateView.as_view(), name='job-create'),
        path('<int:pk>/', std_views.JobDetailView.as_view(), name='job-detail'),
        path('<int:pk>/edit/', std_views.JobUpdateView.as_view(), name='job-edit'),
        path('<int:pk>/status/', std_views.job_update_status, name='job-update-status'),
    ])),

    # Time Tracking (Standard tier)
    path('time/', include([
        path('', std_views.TimeEntryListView.as_view(), name='time-list'),
        path('add/', std_views.TimeEntryCreateView.as_view(), name='time-create'),
        path('<int:pk>/edit/', std_views.TimeEntryUpdateView.as_view(), name='time-edit'),
    ])),
    path('clock-in/', std_views.clock_in, name='clock-in'),
    path('clock-out/', std_views.clock_out, name='clock-out'),

    # Payroll (Standard tier)
    path('payroll/', include([
        path('', std_views.PayPeriodListView.as_view(), name='payperiod-list'),
        path('add/', std_views.PayPeriodCreateView.as_view(), name='payperiod-create'),
        path('<int:pk>/', std_views.PayPeriodDetailView.as_view(), name='payperiod-detail'),
        path('<int:pk>/calculate/', std_views.payroll_calculate, name='payroll-calculate'),
        path('<int:pk>/entry/<int:entry_pk>/', std_views.payroll_entry_edit, name='payroll-entry-edit'),
        path('<int:pk>/stub/<int:entry_pk>/', std_views.pay_stub_pdf, name='paystub-pdf'),
    ])),

    # Estimates (Standard tier)
    path('estimates/', include([
        path('', std_views.EstimateListView.as_view(), name='estimate-list'),
        path('add/', std_views.EstimateCreateView.as_view(), name='estimate-create'),
        path('<int:pk>/', std_views.EstimateDetailView.as_view(), name='estimate-detail'),
        path('<int:pk>/edit/', std_views.EstimateUpdateView.as_view(), name='estimate-edit'),
        path('<int:pk>/convert/', std_views.estimate_convert_to_invoice, name='estimate-convert'),
    ])),

    # API for offline sync
    path('api/invoices/', inv_views.api_invoices, name='api-invoices'),
    path('api/customers/', inv_views.api_customers, name='api-customers'),
    path('api/jobs/', std_views.api_jobs, name='api-jobs'),

    # PWA
    path('manifest.json', pwa_manifest, name='pwa-manifest'),
    path('sw.js', service_worker, name='service-worker'),
    path('offline/', core_views.dashboard, name='offline'),

    # Reporting
    path('reports/', report_views.reports_dashboard, name='reports'),

    # ═══ PREMIUM TIER ═══

    # Recurring Invoices
    path('recurring/', include([
        path('', prem_views.RecurringInvoiceListView.as_view(), name='recurring-list'),
        path('add/', prem_views.RecurringInvoiceCreateView.as_view(), name='recurring-create'),
        path('<int:pk>/', prem_views.RecurringInvoiceDetailView.as_view(), name='recurring-detail'),
        path('<int:pk>/generate/', prem_views.recurring_generate_now, name='recurring-generate'),
    ])),

    # Expenses
    path('expenses/', include([
        path('', prem_views.ExpenseListView.as_view(), name='expense-list'),
        path('add/', prem_views.ExpenseCreateView.as_view(), name='expense-create'),
        path('<int:pk>/edit/', prem_views.ExpenseUpdateView.as_view(), name='expense-edit'),
    ])),

    # Bank Reconciliation
    path('bank/', include([
        path('', prem_views.BankAccountListView.as_view(), name='bank-list'),
        path('add/', prem_views.BankAccountCreateView.as_view(), name='bank-create'),
        path('<int:pk>/', prem_views.BankReconciliationView.as_view(), name='bank-reconcile'),
        path('<int:pk>/import/', prem_views.bank_import_csv, name='bank-import-csv'),
    ])),
    path('bank-match/<int:pk>/', prem_views.bank_match_transaction, name='bank-match'),

    # Purchase Orders
    path('po/', include([
        path('', prem_views.PurchaseOrderListView.as_view(), name='po-list'),
        path('add/', prem_views.PurchaseOrderCreateView.as_view(), name='po-create'),
        path('<int:pk>/', prem_views.PurchaseOrderDetailView.as_view(), name='po-detail'),
    ])),

    # 1099 Contractors
    path('contractors/', include([
        path('', prem_views.ContractorListView.as_view(), name='contractor-list'),
        path('add/', prem_views.ContractorCreateView.as_view(), name='contractor-create'),
        path('<int:pk>/edit/', prem_views.ContractorUpdateView.as_view(), name='contractor-edit'),
    ])),
    path('contractor-payment/add/', prem_views.ContractorPaymentCreateView.as_view(), name='contractor-payment-create'),
    path('1099/<int:contractor_pk>/<int:year>/', prem_views.generate_1099, name='generate-1099'),

    # Tax Forms
    path('tax-forms/', include([
        path('', prem_views.TaxFormListView.as_view(), name='tax-form-list'),
        path('<int:pk>/', prem_views.TaxFormDetailView.as_view(), name='tax-form-detail'),
        path('<int:pk>/pdf/', prem_views.tax_form_pdf, name='tax-form-pdf'),
    ])),

    # Data Import
    path('import/', include([
        path('', prem_views.DataImportListView.as_view(), name='import-list'),
        path('add/', prem_views.DataImportCreateView.as_view(), name='import-create'),
    ])),

    # Contracts
    path('contracts/', include([
        path('', prem_views.ContractListView.as_view(), name='contract-list'),
        path('add/', prem_views.ContractCreateView.as_view(), name='contract-create'),
        path('<int:pk>/', prem_views.ContractDetailView.as_view(), name='contract-detail'),
        path('<int:pk>/send/', prem_views.contract_send, name='contract-send'),
        path('<int:pk>/sign/', prem_views.contract_sign, name='contract-sign'),
    ])),

    # AI Estimate Templates
    path('templates/', include([
        path('', prem_views.EstimateTemplateListView.as_view(), name='template-list'),
        path('add/', prem_views.EstimateTemplateCreateView.as_view(), name='template-create'),
        path('<int:pk>/edit/', prem_views.EstimateTemplateUpdateView.as_view(), name='template-edit'),
    ])),
    path('ai-estimate/<int:template_pk>/', prem_views.ai_estimate, name='ai-estimate'),
]
