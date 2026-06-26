from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum, Count, Avg
from django.db import connection
from django.utils import timezone
from datetime import timedelta
from invoicing.models import Invoice, Payment
from timeclock.models import TimeEntry
from core.models import Customer


class ReportsSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now()
        month_start = today.replace(day=1)
        invoices = Invoice.objects.all()
        payments = Payment.objects.filter(date__gte=month_start)
        data = {
            'total_customers': Customer.objects.filter(is_active=True).count(),
            'total_invoices': invoices.count(),
            'total_revenue_all_time': str(invoices.filter(status='paid').aggregate(t=Sum('total'))['t'] or 0),
            'outstanding_balance': str(invoices.filter(status__in=['sent', 'partial', 'overdue']).aggregate(t=Sum('balance_due'))['t'] or 0),
            'this_month_revenue': str(payments.aggregate(t=Sum('amount'))['t'] or 0),
        }
        return Response(data)


class RevenueReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = timezone.now()
        result = []
        for i in range(12):
            month = today.month - i
            year = today.year
            if month <= 0:
                month += 12
                year -= 1
            total = Payment.objects.filter(date__year=year, date__month=month).aggregate(t=Sum('amount'))['t'] or 0
            result.append({'year': year, 'month': month, 'total': str(total), 'label': f'{year}-{month:02d}'})
        return Response(list(reversed(result)))


class OutstandingReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT inv.invoice_number, c.name, inv.total, inv.balance_due, inv.status, inv.date_created
                FROM invoicing_invoice inv
                LEFT JOIN core_customer c ON inv.customer_id = c.id
                WHERE inv.status IN ('sent', 'partial', 'overdue')
                ORDER BY inv.date_created DESC
            """)
            rows = cursor.fetchall()
        data = [{
            'invoice_number': row[0] or '',
            'customer': row[1] or '',
            'total': str(row[2] or 0),
            'balance_due': str(row[3] or 0),
            'status': row[4] or '',
            'date': str(row[5])[:10] if row[5] else '',
        } for row in rows]
        return Response(data)


class PayrollReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role == 'employee':
            entries = TimeEntry.objects.filter(employee=request.user, time_out__isnull=False)
        else:
            entries = TimeEntry.objects.filter(time_out__isnull=False)

        payroll = {}
        for entry in entries:
            uid = entry.employee_id
            if uid not in payroll:
                payroll[uid] = {
                    'employee': entry.employee.get_full_name() or entry.employee.username,
                    'username': entry.employee.username,
                    'total_hours': 0,
                    'total_earnings': 0,
                }
            payroll[uid]['total_hours'] += float(getattr(entry, 'hours_worked', 0) or 0)
            payroll[uid]['total_earnings'] += float(getattr(entry, 'earnings', 0) or 0)

        result = sorted(payroll.values(), key=lambda x: x['employee'])
        for r in result:
            r['total_hours'] = round(r['total_hours'], 2)
            r['total_earnings'] = round(r['total_earnings'], 2)
        return Response(result)
