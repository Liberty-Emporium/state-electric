from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum
from contracts.models import Contract, ContractLineItem
from contracts.serializers import ContractSerializer, ContractLineItemSerializer


class ContractViewSet(viewsets.ModelViewSet):

    def get_serializer_class(self):
        return ContractSerializer

    def get_queryset(self):
        qs = Contract.objects.select_related('customer').prefetch_related('line_items')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        customer = self.request.query_params.get('customer')
        if customer:
            qs = qs.filter(customer_id=customer)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class ContractDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        contracts = Contract.objects.all()
        by_status = {}
        for status_code, label in Contract.STATUS_CHOICES:
            by_status[status_code] = contracts.filter(status=status_code).count()

        data = {
            'total_contracts': contracts.count(),
            'active_contracts': contracts.filter(status='active').count(),
            'total_value': str(contracts.aggregate(t=Sum('amount'))['t'] or 0),
            'by_status': by_status,
        }
        return Response(data)


class ContractLineItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        contract = Contract.objects.get(pk=pk)
        item = ContractLineItem.objects.create(
            contract=contract,
            description=request.data.get('description', ''),
            quantity=request.data.get('quantity', 1),
            unit_price=request.data.get('unit_price', 0),
        )
        total = sum(li.amount for li in contract.line_items.all())
        contract.amount = total
        contract.save()
        return Response(ContractSerializer(contract).data)
