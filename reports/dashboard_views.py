"""
Dashboard API - Shows real data from the database.
No fake numbers. Only shows what actually exists.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum
from invoicing.models import Invoice, Payment
from core.models import Customer, Vendor, User


class DashboardSummaryView(APIView):
    """Main dashboard KPIs - real numbers only."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        active_customers = Customer.objects.count()
        active_vendors = Vendor.objects.count()
        employees = User.objects.filter(role='employee').count()
        outstanding = Invoice.objects.filter(status__in=['sent', 'partial', 'overdue']).aggregate(t=Sum('balance_due'))['t'] or 0

        return Response({
            'company': 'State Electric & Lighting Co., Inc.',
            'active_customers': active_customers,
            'total_vendors': active_vendors,
            'total_employees': employees,
            'total_invoices': Invoice.objects.count(),
            'outstanding_balance': str(outstanding),
        })


class FinancialGraphsView(APIView):
    """Financial data from actual invoices."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Real invoice data
        paid = Invoice.objects.filter(status='paid').aggregate(t=Sum('total'))['t'] or 0
        outstanding = Invoice.objects.filter(status__in=['sent', 'partial', 'overdue']).aggregate(t=Sum('balance_due'))['t'] or 0

        income_items = []
        expense_items = []

        if paid > 0:
            income_items.append({'label': 'Paid Invoices', 'amount': float(paid)})
        if outstanding > 0:
            expense_items.append({'label': 'Outstanding', 'amount': float(outstanding)})

        return Response({
            'profit_loss': {
                'income': {'items': income_items, 'total': float(paid)},
                'expenses': {'items': expense_items, 'total': float(outstanding)},
            },
            'balance_sheet': {
                'assets': {'items': income_items, 'total': float(paid)},
                'liabilities': {'items': expense_items, 'total': float(outstanding)},
            },
        })


class RevenueTrendView(APIView):
    """Monthly revenue from actual payments."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.db.models.functions import TruncMonth
        monthly = Payment.objects.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(total=Sum('amount')).order_by('month')[:12]

        return Response([{
            'month': m['month'].strftime('%Y-%m') if m['month'] else '',
            'revenue': float(m['total'] or 0),
            'label': m['month'].strftime('%b %Y') if m['month'] else '',
        } for m in monthly])


class TopCustomersView(APIView):
    """Top customers by actual invoice totals."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        top = Invoice.objects.values('customer__name').annotate(
            total_revenue=Sum('total')
        ).filter(total_revenue__gt=0).order_by('-total_revenue')[:20]

        if top:
            return Response([
                {'customer': t['customer__name'], 'total_revenue': float(t['total_revenue'] or 0)}
                for t in top
            ])

        # No invoices yet — show customers with note
        customers = Customer.objects.all().order_by('name')[:20]
        return Response([
            {'customer': c.name, 'total_revenue': 0}
            for c in customers
        ])


class RecentActivityView(APIView):
    """Recent invoices from database."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        invoices = Invoice.objects.select_related('customer').order_by('-date_created')[:20]
        return Response([{
            'date': str(inv.date_created)[:10],
            'type': 'Invoice',
            'name': inv.customer.name if inv.customer else '',
            'account': inv.invoice_number,
            'debit': 0,
            'credit': float(inv.total or 0),
        } for inv in invoices])


class AIQueryView(APIView):
    """Answer questions with real data."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').lower()
        response = {'query': query, 'answer': '', 'data': None}

        if 'customer' in query and ('count' in query or 'many' in query):
            count = Customer.objects.count()
            response['answer'] = f"You have {count} customers."
        elif 'vendor' in query and ('count' in query or 'many' in query):
            count = Vendor.objects.count()
            response['answer'] = f"You have {count} vendors."
        elif 'employee' in query and ('count' in query or 'many' in query):
            count = User.objects.filter(role='employee').count()
            response['answer'] = f"You have {count} employees."
        elif 'invoice' in query and ('count' in query or 'many' in query):
            count = Invoice.objects.count()
            response['answer'] = f"You have {count} invoices in the system."
        elif 'outstanding' in query or 'unpaid' in query:
            total = Invoice.objects.filter(status__in=['sent', 'partial', 'overdue']).aggregate(t=Sum('balance_due'))['t'] or 0
            response['answer'] = f"Outstanding balance: ${float(total):,.2f}"
        elif 'revenue' in query or 'income' in query:
            total = Invoice.objects.filter(status='paid').aggregate(t=Sum('total'))['t'] or 0
            response['answer'] = f"Total paid revenue: ${float(total):,.2f}"
        elif 'top' in query and 'customer' in query:
            top = Invoice.objects.values('customer__name').annotate(
                total_revenue=Sum('total')
            ).filter(total_revenue__gt=0).order_by('-total_revenue')[:10]
            if top:
                response['answer'] = f"Your top {len(top)} customers by revenue:"
                response['data'] = [{'customer': t['customer__name'], 'revenue': float(t['total_revenue'] or 0)} for t in top]
            else:
                response['answer'] = "No invoice data yet. Import QuickBooks invoices to see revenue by customer."
        else:
            response['answer'] = "Try: 'How many customers?', 'How many vendors?', 'How many employees?', 'Outstanding balance?', 'Total revenue?'"

        return Response(response)
