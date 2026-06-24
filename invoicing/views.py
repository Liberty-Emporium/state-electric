from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count
from django.utils import timezone
from invoicing.models import Invoice, InvoiceLineItem, Payment
from invoicing.serializers import InvoiceSerializer, InvoiceLineItemSerializer, PaymentSerializer


class InvoiceViewSet(viewsets.ModelViewSet):
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        qs = Invoice.objects.select_related('customer').prefetch_related('line_items', 'payments')
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        customer = self.request.query_params.get('customer')
        if customer:
            qs = qs.filter(customer_id=customer)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class OutstandingInvoicesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        invoices = Invoice.objects.filter(status__in=['sent', 'partial', 'overdue'])
        data = {
            'count': invoices.count(),
            'total_outstanding': str(invoices.aggregate(t=Sum('balance_due'))['t'] or 0),
            'invoices': InvoiceSerializer(invoices, many=True).data,
        }
        return Response(data)


class AddPaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        invoice = Invoice.objects.get(pk=pk)
        amount = request.data.get('amount')
        try:
            amount = float(amount)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid amount'}, status=400)

        payment = Payment.objects.create(
            invoice=invoice,
            amount=amount,
            method=request.data.get('method', 'check'),
            reference=request.data.get('reference', ''),
            notes=request.data.get('notes', ''),
            recorded_by=request.user,
        )
        invoice.save()  # recalculates balance
        return Response(PaymentSerializer(payment).data)


class InvoiceLineItemView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        invoice = Invoice.objects.get(pk=pk)
        item = InvoiceLineItem.objects.create(
            invoice=invoice,
            description=request.data.get('description', ''),
            quantity=request.data.get('quantity', 1),
            unit_price=request.data.get('unit_price', 0),
        )
        # Recalculate invoice
        total = sum(li.amount for li in invoice.line_items.all())
        invoice.subtotal = total
        invoice.total = total + invoice.tax_amount
        invoice.save()
        return Response(InvoiceLineItemSerializer(item).data)


class InvoiceDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now()
        invoices = Invoice.objects.all()
        data = {
            'total_invoices': invoices.count(),
            'draft': invoices.filter(status='draft').count(),
            'sent': invoices.filter(status='sent').count(),
            'paid': invoices.filter(status='paid').count(),
            'overdue': invoices.filter(status='overdue').count(),
            'total_revenue': str(invoices.filter(status='paid').aggregate(t=Sum('total'))['t'] or 0),
            'total_outstanding': str(invoices.filter(status__in=['sent', 'partial', 'overdue']).aggregate(t=Sum('balance_due'))['t'] or 0),
        }
        return Response(data)
