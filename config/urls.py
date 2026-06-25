from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({'status': 'ok', 'service': 'State Electric API'})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check),
    path('api/auth/', include('core.urls')),
    path('api/customers/', include('core.customer_urls')),
    path('api/vendors/', include('core.vendor_urls')),
    path('api/invoices/', include('invoicing.urls')),
    path('api/payments/', include('invoicing.payment_urls')),
    path('api/time/', include('timeclock.urls')),
    path('api/files/', include('files.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/contracts/', include('contracts.urls')),
    path('api/payroll/', include('payroll.urls')),
]
