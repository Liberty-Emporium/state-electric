"""
Views for uploading documents to the volume.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import render
from files.models import BusinessDocument
from core.models import Customer
import os


@csrf_exempt
@require_POST
def upload_document(request):
    """Upload a document file and create a database record."""
    if not request.FILES.get('file'):
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    uploaded_file = request.FILES['file']
    title = request.POST.get('title', uploaded_file.name)[:200]
    category = request.POST.get('category', 'other')
    folder = request.POST.get('folder', 'Uploaded')
    customer_id = request.POST.get('customer_id')
    
    valid_categories = [c[0] for c in BusinessDocument.CATEGORY_CHOICES]
    if category not in valid_categories:
        category = 'other'
    
    doc = BusinessDocument(
        title=title,
        category=category,
        folder=folder,
        description="Uploaded via web interface",
    )
    
    if customer_id:
        try:
            doc.customer = Customer.objects.get(pk=customer_id)
        except (Customer.DoesNotExist, ValueError):
            pass
    
    doc.file = uploaded_file
    doc.save()
    
    return JsonResponse({
        'success': True,
        'id': doc.id,
        'title': doc.title,
        'category': doc.category,
        'folder': doc.folder,
        'url': doc.file.url,
    })


def upload_page(request):
    """Render the upload page."""
    return render(request, 'files/upload.html')
