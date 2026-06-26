from django.urls import path
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from core.models import Vendor


class VendorListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        vendors = Vendor.objects.all().order_by('name')
        data = []
        for v in vendors:
            data.append({
                'id': v.id,
                'name': v.name or '',
                'company': getattr(v, 'company', '') or '',
                'contact_name': getattr(v, 'contact_name', '') or '',
                'phone': v.phone or '',
                'email': v.email or '',
                'address': getattr(v, 'address', '') or '',
                'notes': getattr(v, 'notes', '') or '',
                'is_active': getattr(v, 'is_active', True),
            })
        return Response(data)


class VendorDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            v = Vendor.objects.get(pk=pk)
        except Vendor.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        return Response({
            'id': v.id,
            'name': v.name or '',
            'contact_name': getattr(v, 'contact_name', '') or '',
            'phone': v.phone or '',
            'email': v.email or '',
            'address': getattr(v, 'address', '') or '',
            'is_active': getattr(v, 'is_active', True),
        })


urlpatterns = [
    path('', VendorListView.as_view()),
    path('<int:pk>/', VendorDetailView.as_view()),
]
