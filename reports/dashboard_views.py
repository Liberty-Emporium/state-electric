"""
Dashboard API - Financial graphs, KPIs, and business intelligence.
"""
import os
import sys
import json
from datetime import datetime, timedelta
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.utils import timezone
from invoicing.models import Invoice, Payment
from core.models import Customer


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
        today = timezone.now()
        month_start = today.replace(day=1)
        
        # Live data from Django models
        try:
            today_invoices = Invoice.objects.count() or 0
        except:
            today_invoices = 0
        try:
            outstanding = Invoice.objects.filter(
                status__in=['sent', 'partial', 'overdue']
            ).aggregate(t=connection.ops.coalesce_func(Sum('balance_due'), 0))['t'] or 0
        except:
            from django.db.models import Sum
            outstanding = Invoice.objects.filter(
                status__in=['sent', 'partial', 'overdue']
            ).aggregate(t=Sum('balance_due'))['t'] or 0
        
        active_customers = Customer.objects.count()
        
        # QB Data summary
        qb_data = load_qb_data()
        qb_customer_count = len(qb_data.get('customers', []))
        qb_vendor_count = len(qb_data.get('vendors', []))
        qb_employee_count = len(qb_data.get('employees', []))
        
        # Financial totals from QB
        bs = qb_data.get('balance_sheet', [])
        total_assets = sum(b['amount'] for b in b['account'] in ('ASSETS', 'Total Assets') for b in [b])
        total_income = sum(p['amount'] for p in qb_data.get('profit_loss', []) if p['account'] in ('Income', 'Total Income'))
        total_expenses = sum(p['amount'] for p in qb_data.get('profit_loss', []) if p['account'] in ('Expenses', 'Total Expenses'))
        
        return Response({
            'company': 'State Electric & Lighting Co., Inc.',
            'active_customers': active_customers,
            'total_customers_qb': qb_customer_count,
            'total_vendors': qb_vendor_count,
            'total_employees': qb_employee_count,
            'total_invoices': today_invoices,
            'outstanding_balance': str(outstanding),
            'qb_total_income': total_income,
            'qb_total_expenses': total_expenses,
            'qb_net_income': total_income - total_expenses,
            'data_imported_at': timezone.now().isoformat(),
        })


class FinancialGraphsView(APIView):
    """Financial graphs data - Profit & Loss breakdown."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qb_data = load_qb_data()
        period = request.query_params.get('period', 'all')
        
        # Profit & Loss categories
        pl_data = qb_data.get('profit_loss', [])
        income_items = []
        expense_items = []
        income_total = 0
        expense_total = 0
        
        for item in pl_data:
            account = item.get('account', '').strip()
            amount = item.get('amount', 0)
            if not account or account in ('Income', 'Total Income', 'Expenses', 'Total Expenses', 'Net Income'):
                continue
            
            # Simple categorization based on account name
            if any(word in account.lower() for word in ['income', 'sales', 'service', 'revenue', 'deposit']):
                income_items.append({'label': account, 'amount': amount})
                income_total += amount
            elif any(word in account.lower() for word in ['expense', 'cost', 'supplies', 'payroll', 'tax', 'insurance', 'rent', 'utilities', 'fuel', 'advertising', 'office', 'professional', 'travel', 'meals', 'bank']):
                expense_items.append({'label': account, 'amount': amount})
                expense_total += amount
        
        # Balance Sheet categories
        bs_data = qb_data.get('balance_sheet', [])
        assets = []
        liabilities = []
        equity = []
        asset_total = 0
        liability_total = 0
        equity_total = 0
        
        section = None
        for item in bs_data:
            account = item.get('account', '').strip()
            amount = item.get('amount', 0)
            
            # Track sections
            acc_lower = account.lower()
            if 'asset' in acc_lower:
                section = 'assets'
                continue
            elif 'liabilit' in acc_lower or 'liabilities' in acc_lower:
                section = 'liabilities'
                continue
            elif 'equity' in acc_lower or 'capital' in acc_lower:
                section = 'equity'
                continue
            
            if section == 'assets' and amount != 0:
                assets.append({'label': account, 'amount': amount})
                asset_total += amount
            elif section == 'liabilities' and amount != 0:
                liabilities.append({'label': account, 'amount': amount})
                liability_total += amount
            elif section == 'equity' and amount != 0:
                equity.append({'label': account, 'amount': amount})
                equity_total += amount
        
        return Response({
            'profit_loss': {
                'income': {'items': sorted(income_items, key=lambda x: -x['amount'])[:10], 'total': income_total},
                'expenses': {'items': sorted(expense_items, key=lambda x: -x['amount'])[:10], 'total': expense_total},
                'net_income': income_total - expense_total,
            },
            'balance_sheet': {
                'assets': {'items': sorted(assets, key=lambda x: -x['amount'])[:10], 'total': asset_total},
                'liabilities': {'items': sorted(liabilities, key=lambda x: -x['amount'])[:10], 'total': liability_total},
                'equity': {'items': sorted(equity, key=lambda x: -x['amount'])[:10], 'total': equity_total},
            },
        })


class RevenueTrendView(APIView):
    """Monthly revenue trend from QB General Ledger."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qb_data = load_qb_data()
        gl = qb_data.get('general_ledger', [])
        
        # Aggregate deposits/revenue by month
        monthly = {}
        for entry in gl:
            date_str = entry.get('date', '')
            tx_type = entry.get('type', '').lower()
            credit = entry.get('credit', 0)
            
            # Look for revenue-related transactions
            if tx_type in ('deposit', 'payment', 'invoice') and credit > 0:
                try:
                    if isinstance(date_str, str) and len(date_str) >= 7:
                        month_key = date_str[:7]  # YYYY-MM format
                    else:
                        continue
                    if month_key not in monthly:
                        monthly[month_key] = 0
                    monthly[month_key] += credit
                except:
                    continue
        
        # Sort by month and format
        sorted_months = sorted(monthly.items())[-12:]  # Last 12 months
        data = [{'month': m, 'revenue': r, 'label': m} for m, r in sorted_months]
        
        return Response(data)


class TopCustomersView(APIView):
    """Top customers by number of invoices/deposits."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qb_data = load_qb_data()
        gl = qb_data.get('general_ledger', [])
        
        customer_totals = {}
        for entry in gl:
            name = entry.get('name', '').strip()
            credit = entry.get('credit', 0)
            if name and credit > 0:
                if name not in customer_totals:
                    customer_totals[name] = 0
                customer_totals[name] += credit
        
        top = sorted(customer_totals.items(), key=lambda x: -x[1])[:20]
        data = [{'customer': name, 'total_revenue': total, 'label': name[:30]} for name, total in top]
        
        return Response(data)


class RecentActivityView(APIView):
    """Recent transactions and activity."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qb_data = load_qb_data()
        gl = qb_data.get('general_ledger', [])
        
        # Get most recent transactions
        recent = []
        for entry in reversed(gl[-50:]):  # Last 50 entries
            if entry.get('debit', 0) > 0 or entry.get('credit', 0) > 0:
                recent.append({
                    'date': entry.get('date', ''),
                    'type': entry.get('type', ''),
                    'name': entry.get('name', ''),
                    'account': entry.get('account', ''),
                    'debit': entry.get('debit', 0),
                    'credit': entry.get('credit', 0),
                })
        
        return Response(recent[:20])


class AIQueryView(APIView):
    """Simple AI-like query endpoint - answers basic questions."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '').lower()
        
        qb_data = load_qb_data()
        response = {'query': query, 'answer': '', 'data': None}
        
        # Answer common business questions
        if 'customer' in query and 'count' in query:
            count = len(qb_data.get('customers', []))
            response['answer'] = f"You have {count} customers in QuickBooks."
            response['data'] = {'total_customers': count}
            
        elif 'vendor' in query and 'count' in query:
            count = len(qb_data.get('vendors', []))
            response['answer'] = f"You have {count} vendors in QuickBooks."
            response['data'] = {'total_vendors': count}
            
        elif 'employee' in query and 'count' in query:
            count = len(qb_data.get('employees', []))
            response['answer'] = f"You have {count} employees in QuickBooks."
            response['data'] = {'total_employees': count}
            
        elif 'income' in query or 'revenue' in query:
            pl = qb_data.get('profit_loss', [])
            total = sum(p.get('amount', 0) for p in pl if 'income' in p.get('account', '').lower() or 'sales' in p.get('account', '').lower())
            response['answer'] = f"Total income/revenue: ${total:,.2f}"
            response['data'] = {'total_income': total}
            
        elif 'expense' in query:
            pl = qb_data.get('profit_loss', [])
            total = sum(abs(p.get('amount', 0)) for p in pl if 'expense' in p.get('account', '').lower() or 'cost' in p.get('account', '').lower())
            response['answer'] = f"Total expenses: ${total:,.2f}"
            response['data'] = {'total_expenses': total}
            
        elif 'asset' in query:
            bs = qb_data.get('balance_sheet', [])
            total = sum(b.get('amount', 0) for b in bs if 'asset' in b.get('account', '').lower())
            response['answer'] = f"Total assets: ${total:,.2f}"
            response['data'] = {'total_assets': total}
            
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
            response['answer'] = "Try asking: 'How many customers?' 'Total income?' 'Top customers?' 'Total assets?'"
        
        return Response(response)
