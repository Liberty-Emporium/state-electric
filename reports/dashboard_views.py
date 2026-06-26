"""
Dashboard API - Financial graphs, KPIs, and business intelligence.
"""
import os
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.utils import timezone
from invoicing.models import Invoice, Payment
from core.models import Customer, User


def load_qb_data():
    """Load parsed QuickBooks data."""
    data_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'state-electric-data', 'parsed_qb_data.json'
    )
    if os.path.exists(data_file):
        with open(data_file) as f:
            return json.load(f)
    return {}


class DashboardSummaryView(APIView):
    """Main dashboard KPIs."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qb_data = load_qb_data()
        return Response({
            'company': 'State Electric & Lighting Co., Inc.',
            'active_customers': Customer.objects.filter(is_active=True).count(),
            'total_customers_qb': len(qb_data.get('customers', [])),
            'total_vendors': len(qb_data.get('vendors', [])),
            'total_employees': len(qb_data.get('employees', [])),
            'total_invoices': Invoice.objects.count(),
            'outstanding_balance': str(
                Invoice.objects.filter(status__in=['sent', 'partial', 'overdue'])
                .values_list('balance_due', flat=True)
                .count() and
                sum(Invoice.objects.filter(status__in=['sent', 'partial', 'overdue']).values_list('balance_due', flat=True)) or 0
            ),
        })


class FinancialGraphsView(APIView):
    """Financial graphs data."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qb_data = load_qb_data()

        # Profit & Loss
        pl_data = qb_data.get('profit_loss', [])
        income_items = []
        expense_items = []
        for item in pl_data:
            account = item.get('account', '').strip()
            amount = item.get('amount', 0)
            if not account or amount == 0:
                continue
            if any(w in account.lower() for w in ['income', 'sales', 'service', 'revenue']):
                income_items.append({'label': account[:40], 'amount': amount})
            elif any(w in account.lower() for w in ['expense', 'cost', 'supplies', 'payroll', 'tax', 'insurance']):
                expense_items.append({'label': account[:40], 'amount': abs(amount)})

        # Balance Sheet
        bs_data = qb_data.get('balance_sheet', [])
        assets = []
        liabilities = []
        section = None
        for item in bs_data:
            account = item.get('account', '').strip()
            amount = item.get('amount', 0)
            if 'asset' in account.lower():
                section = 'assets'
                continue
            elif 'liabilit' in account.lower():
                section = 'liabilities'
                continue
            elif section == 'assets' and amount != 0:
                assets.append({'label': account[:40], 'amount': amount})
            elif section == 'liabilities' and amount != 0:
                liabilities.append({'label': account[:40], 'amount': abs(amount)})

        return Response({
            'profit_loss': {
                'income': {'items': sorted(income_items, key=lambda x: -x['amount'])[:10], 'total': sum(i['amount'] for i in income_items)},
                'expenses': {'items': sorted(expense_items, key=lambda x: -x['amount'])[:10], 'total': sum(i['amount'] for i in expense_items)},
            },
            'balance_sheet': {
                'assets': {'items': sorted(assets, key=lambda x: -x['amount'])[:10], 'total': sum(i['amount'] for i in assets)},
                'liabilities': {'items': sorted(liabilities, key=lambda x: -x['amount'])[:10], 'total': sum(i['amount'] for i in liabilities)},
            },
        })


class RevenueTrendView(APIView):
    """Monthly revenue trend."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qb_data = load_qb_data()
        gl = qb_data.get('general_ledger', [])
        monthly = {}
        for entry in gl:
            date_str = entry.get('date', '')
            credit = entry.get('credit', 0)
            if credit > 0 and isinstance(date_str, str) and len(date_str) >= 7:
                month_key = date_str[:7]
                monthly[month_key] = monthly.get(month_key, 0) + credit
        sorted_months = sorted(monthly.items())[-12:]
        return Response([{'month': m, 'revenue': r, 'label': m} for m, r in sorted_months])


class TopCustomersView(APIView):
    """Top customers by revenue."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qb_data = load_qb_data()
        gl = qb_data.get('general_ledger', [])
        cust = {}
        for entry in gl:
            name = entry.get('name', '').strip()
            credit = entry.get('credit', 0)
            if name and credit > 0:
                cust[name] = cust.get(name, 0) + credit
        top = sorted(cust.items(), key=lambda x: -x[1])[:20]
        return Response([{'customer': n, 'total_revenue': r} for n, r in top])


class RecentActivityView(APIView):
    """Recent transactions."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qb_data = load_qb_data()
        gl = qb_data.get('general_ledger', [])
        recent = []
        for entry in reversed(gl[-50:]):
            if entry.get('debit', 0) > 0 or entry.get('credit', 0) > 0:
                recent.append({
                    'date': str(entry.get('date', ''))[:10],
                    'type': entry.get('type', ''),
                    'name': entry.get('name', ''),
                    'account': entry.get('account', ''),
                    'debit': entry.get('debit', 0),
                    'credit': entry.get('credit', 0),
                })
        return Response(recent[:20])


class AIQueryView(APIView):
    """Simple query endpoint."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').lower()
        qb_data = load_qb_data()
        response = {'query': query, 'answer': '', 'data': None}

        if 'customer' in query and ('count' in query or 'many' in query):
            count = len(qb_data.get('customers', []))
            response['answer'] = f"You have {count} customers in QuickBooks."
            response['data'] = {'total_customers': count}
        elif 'vendor' in query and ('count' in query or 'many' in query):
            count = len(qb_data.get('vendors', []))
            response['answer'] = f"You have {count} vendors."
            response['data'] = {'total_vendors': count}
        elif 'employee' in query and ('count' in query or 'many' in query):
            count = len(qb_data.get('employees', []))
            response['answer'] = f"You have {count} employees."
            response['data'] = {'total_employees': count}
        elif 'income' in query or 'revenue' in query:
            response['answer'] = "Income data is available in the Reports section."
        elif 'expense' in query:
            response['answer'] = "Expense data is available in the Reports section."
        elif 'top' in query and 'customer' in query:
            gl = qb_data.get('general_ledger', [])
            cust = {}
            for e in gl:
                n = e.get('name', '')
                c = e.get('credit', 0)
                if n and c > 0:
                    cust[n] = cust.get(n, 0) + c
            top = sorted(cust.items(), key=lambda x: -x[1])[:10]
            response['answer'] = f"Your top {len(top)} customers by revenue:"
            response['data'] = [{'customer': n, 'revenue': r} for n, r in top]
        else:
            response['answer'] = "Try: 'How many customers?', 'Top customers?', 'Total vendors?', 'Total employees?'"

        return Response(response)
