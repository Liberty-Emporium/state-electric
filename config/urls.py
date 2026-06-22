"""URL configuration for State Electric."""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

from core import views as core_views
from core.pwa_views import pwa_manifest, service_worker
from invoicing import views as inv_views
from reporting import views as report_views
from standard import views as std_views

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
]
