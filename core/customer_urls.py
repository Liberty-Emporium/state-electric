from django.urls import path
from rest_framework import generics, permissions, viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum
from core.models import Customer


class CustomerViewSet(viewsets.ModelViewSet):

    def get_serializer_class(self):
        from core.serializers import CustomerSerializer
        return CustomerSerializer

    def get_serializer(self, *args, **kwargs):
        from core.serializers import CustomerSerializer
        return CustomerSerializer(*args, **kwargs)

    def get_queryset(self):
        qs = Customer.objects.all()
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


class CustomerOutstandingView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.serializers import CustomerSerializer
        customers = Customer.objects.filter(is_active=True).annotate(
            balance=Sum('invoices__balance_due')
        ).filter(balance__gt=0).order_by('-balance')
        data = CustomerSerializer(customers, many=True).data
        for c in data:
            c['outstanding_balance'] = str(c.get('outstanding_balance', '0'))
        return Response(data)


urlpatterns = [
    path('', CustomerViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('<int:pk>/', CustomerViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'})),
    path('outstanding/', CustomerOutstandingView.as_view()),
]
