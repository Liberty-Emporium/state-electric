"""URL configuration for State Electric."""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

from core import views as core_views
from core.pwa_views import pwa_manifest, service_worker
from invoicing import views as inv_views
from reporting import views as report_views

urlpatterns = [
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

    # API for offline sync
    path('api/invoices/', inv_views.api_invoices, name='api-invoices'),
    path('api/customers/', inv_views.api_customers, name='api-customers'),

    # PWA
    path('manifest.json', pwa_manifest, name='pwa-manifest'),
    path('sw.js', service_worker, name='service-worker'),
    path('offline/', core_views.dashboard, name='offline'),  # Placeholder — renders dashboard which will show cached data

    # Reporting
    path('reports/', report_views.reports_dashboard, name='reports'),
]
