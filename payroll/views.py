from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum
from payroll.models import PayrollRun, Paystub, TaxRate
from payroll.serializers import PayrollRunSerializer, PaystubSerializer, TaxRateSerializer


class PayrollRunViewSet(viewsets.ModelViewSet):
    def get_serializer_class(self):
        return PayrollRunSerializer

    def get_queryset(self):
        qs = PayrollRun.objects.prefetch_related('paystubs__employee')
        status = self.request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

    def perform_create(self, serializer):
        serializer.save(processed_by=self.request.user)


class PaystubViewSet(viewsets.ModelViewSet):
    serializer_class = PaystubSerializer

    def get_queryset(self):
        qs = Paystub.objects.select_related('employee', 'payroll_run')
        # Employees only see their own paystubs
        if self.request.user.role == 'employee':
            qs = qs.filter(employee=self.request.user)
        return qs


class MyPaystubsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        paystubs = Paystub.objects.filter(employee=request.user).select_related('payroll_run')
        return Response(PaystubSerializer(paystubs, many=True).data)


class TaxRateViewSet(viewsets.ModelViewSet):
    serializer_class = TaxRateSerializer
    queryset = TaxRate.objects.all()

    def get_permissions(self):
        if self.request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]
