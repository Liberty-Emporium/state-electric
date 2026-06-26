from django.urls import path
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from core.models import Customer


class CustomerListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        customers = Customer.objects.all().order_by('name')
        data = []
        for c in customers:
            data.append({
                'id': c.id,
                'name': c.name or '',
                'company': getattr(c, 'company', '') or '',
                'contact_name': getattr(c, 'contact_name', '') or '',
                'phone': c.phone or '',
                'email': c.email or '',
                'billing_address': getattr(c, 'billing_address', '') or '',
                'shipping_address': getattr(c, 'shipping_address', '') or '',
                'notes': getattr(c, 'notes', '') or '',
                'is_active': getattr(c, 'is_active', True),
                'outstanding_balance': str(getattr(c, 'outstanding_balance', 0) or 0),
            })
        return Response(data)


class CustomerDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            c = Customer.objects.get(pk=pk)
        except Customer.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)
        return Response({
            'id': c.id,
            'name': c.name or '',
            'company': getattr(c, 'company', '') or '',
            'contact_name': getattr(c, 'contact_name', '') or '',
            'phone': c.phone or '',
            'email': c.email or '',
            'billing_address': getattr(c, 'billing_address', '') or '',
            'shipping_address': getattr(c, 'shipping_address', '') or '',
            'notes': getattr(c, 'notes', '') or '',
            'is_active': getattr(c, 'is_active', True),
        })


urlpatterns = [
    path('', CustomerListView.as_view()),
    path('<int:pk>/', CustomerDetailView.as_view()),
]
