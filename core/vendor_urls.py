from django.urls import path
from rest_framework import generics, permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from core.models import Vendor


class VendorViewSet(viewsets.ModelViewSet):

    def get_serializer_class(self):
        from core.serializers import VendorSerializer
        return VendorSerializer

    def get_serializer(self, *args, **kwargs):
        from core.serializers import VendorSerializer
        return VendorSerializer(*args, **kwargs)

    def get_queryset(self):
        qs = Vendor.objects.all()
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(name__icontains=search) | qs.filter(contact_name__icontains=search)
        active_only = self.request.query_params.get('active', 'true')
        if active_only == 'true':
            qs = qs.filter(is_active=True)
        return qs

    def get_permissions(self):
        if self.request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]


urlpatterns = [
    path('', VendorViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('<int:pk>/', VendorViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),
]
