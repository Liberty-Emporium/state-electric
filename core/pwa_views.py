"""PWA views — manifest and service worker."""
import json
from django.http import JsonResponse
from django.views.decorators.cache import cache_page


@cache_page(60 * 60 * 24)  # Cache for 24 hours
def pwa_manifest(request):
    """Serve the PWA web app manifest."""
    manifest = {
        "name": "State Electric",
        "short_name": "StateElectric",
        "description": "Business Management for Electrical Contractors",
        "start_url": "/dashboard/",
        "display": "standalone",
        "background_color": "#0f172a",
        "theme_color": "#1e3a5f",
        "orientation": "portrait-primary",
        "icons": [
            {
                "src": "/static/img/icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/img/icon-512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }
    return JsonResponse(manifest, content_type="application/manifest+json")


@cache_page(60 * 60 * 24)
def service_worker(request):
    """Serve the service worker for offline caching."""
    from django.template.loader import render_to_string
    from django.http import HttpResponse
    html = render_to_string('sw.js', request=request)
    return HttpResponse(html, content_type="application/javascript")
