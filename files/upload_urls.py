from django.urls import path
from . import upload_views

urlpatterns = [
    path('upload/', upload_views.upload_page, name='upload_page'),
    path('api/upload/', upload_views.upload_document, name='upload_document'),
]
