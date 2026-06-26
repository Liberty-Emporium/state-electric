"""
Dashboard API - Financial graphs, KPIs, and business intelligence.
All data comes from the live database.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db import connection
from django.db.models import Sum
from django.utils import timezone
from invoicing.models import Invoice, Payment
from core.models import Customer, Vendor, User


class DashboardSummaryView(APIView):
    """Main dashboard KPIs."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            'company': 'State Electric & Lighting Co., Inc.',
            'active_customers': Customer.objects.filter(is_active=True).count(),
            'total_customers_qb': Customer.objects.count(),
            'total_vendors': Vendor.objects.count(),
            'total_employees': User.objects.filter(role='employee', is_active=True).count(),
            'total_invoices': Invoice.objects.count(),
            'outstanding_balance': str(
                Invoice.objects.filter(status__in=['sent', 'partial', 'overdue'])
                .aggregate(t=Sum('balance_due'))['t'] or 0
            ),
        })


class FinancialGraphsView(APIView):
    """Financial graphs data from database."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get income/expense from invoices
        paid_invoices = Invoice.objects.filter(status='paid')
        total_revenue = paid_invoices.aggregate(t=Sum('total'))['t'] or 0

        # For now, show revenue as income
        income_items = []
        if total_revenue > 0:
            income_items.append({'label': 'Total Revenue', 'amount': float(total_revenue)})

        # Get invoice totals by customer for expense breakdown
        top_invoices = Invoice.objects.values('customer__name').annotate(
            total=Sum('total')
        ).order_by('-total')[:10]

        expense_items = []
        for inv in top_invoices:
            if inv['customer__name'] and inv['total']:
                expense_items.append({'label': inv['customer__name'][:40], 'amount': float(inv['total'])})

        return Response({
            'profit_loss': {
                'income': {'items': income_items, 'total': float(total_revenue)},
                'expenses': {'items': expense_items, 'total': sum(i['amount'] for i in expense_items)},
            },
            'balance_sheet': {
                'assets': {'items': income_items[:5], 'total': float(total_revenue)},
                'liabilities': {'items': [], 'total': 0},
            },
        })


class RevenueTrendView(APIView):
    """Monthly revenue trend from database."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.db.models.functions import TruncMonth
        from django.db.models import Sum

        monthly = Invoice.objects.filter(status='paid').annotate(
            month=TruncMonth('date_created')
        ).values('month').annotate(total=Sum('total')).order_by('month')[:12]

        result = []
        for m in monthly:
            if m['month']:
                result.append({
                    'month': m['month'].strftime('%Y-%m'),
                    'revenue': float(m['total'] or 0),
                    'label': m['month'].strftime('%Y-%m'),
                })
        return Response(result)


class TopCustomersView(APIView):
    """Top customers by invoice total."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        top = Invoice.objects.values('customer__name').annotate(
            total_revenue=Sum('total')
        ).filter(total_revenue__gt=0).order_by('-total_revenue')[:20]

        return Response([
            {'customer': t['customer__name'], 'total_revenue': float(t['total_revenue'] or 0)}
            for t in top
        ])


class RecentActivityView(APIView):
    """Recent invoices."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT inv.date_created, c.name, inv.invoice_number, inv.total
                FROM invoicing_invoice inv
                LEFT JOIN core_customer c ON inv.customer_id = c.id
                ORDER BY inv.created_at DESC NULLS LAST
                LIMIT 20
            """)
            rows = cursor.fetchall()
        return Response([{
            'date': str(row[0])[:10] if row[0] else '',
            'type': 'Invoice',
            'name': row[1] or '',
            'account': row[2] or '',
            'debit': 0,
            'credit': float(row[3] or 0),
        } for row in rows])


class AIQueryView(APIView):
    """Simple query endpoint."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').lower()
        response = {'query': query, 'answer': '', 'data': None}

        if 'customer' in query and ('count' in query or 'many' in query):
            count = Customer.objects.count()
            response['answer'] = f"You have {count} customers."
            response['data'] = {'total_customers': count}
        elif 'vendor' in query and ('count' in query or 'many' in query):
            count = Vendor.objects.count()
            response['answer'] = f"You have {count} vendors."
            response['data'] = {'total_vendors': count}
        elif 'employee' in query and ('count' in query or 'many' in query):
            count = User.objects.filter(role='employee').count()
            response['answer'] = f"You have {count} employees."
            response['data'] = {'total_employees': count}
        elif 'invoice' in query and ('count' in query or 'many' in query):
            count = Invoice.objects.count()
            response['answer'] = f"You have {count} invoices."
            response['data'] = {'total_invoices': count}
        elif 'top' in query and 'customer' in query:
            top = Invoice.objects.values('customer__name').annotate(
                total_revenue=Sum('total')
            ).filter(total_revenue__gt=0).order_by('-total_revenue')[:10]
            response['answer'] = f"Your top {len(top)} customers by revenue:"
            response['data'] = [{'customer': t['customer__name'], 'revenue': float(t['total_revenue'] or 0)} for t in top]
        elif 'outstanding' in query or 'unpaid' in query:
            total = Invoice.objects.filter(status__in=['sent', 'partial', 'overdue']).aggregate(t=Sum('balance_due'))['t'] or 0
            response['answer'] = f"Outstanding balance: ${float(total):,.2f}"
            response['data'] = {'outstanding': float(total)}
        else:
            response['answer'] = "Try: 'How many customers?', 'Top customers?', 'Total vendors?', 'How many employees?', 'Outstanding balance?'"

        return Response(response)
