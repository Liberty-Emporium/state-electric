from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse, HttpResponse
from django.views.generic import TemplateView
from django.conf import settings
import os

def health_check(request):
    return JsonResponse({'status': 'ok', 'service': 'State Electric API'})

def serve_app(request):
    """Serve the main SPA."""
    index_path = os.path.join(settings.BASE_DIR, 'static', 'index.html')
    with open(index_path, 'r') as f:
        return HttpResponse(f.read())

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
