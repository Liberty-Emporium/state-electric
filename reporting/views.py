"""Reporting views for State Electric."""
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta

from core.models import Customer, Division, Invoice, Payment
from core.views import get_user_divisions


@login_required
def reports_dashboard(request):
    """Reports dashboard with revenue, AR, and division breakdown."""
    user = request.user
    divisions = get_user_divisions(user)

    # Base querysets
    invoice_qs = Invoice.objects.all()
    payment_qs = Payment.objects.all()
    customer_qs = Customer.objects.filter(is_active=True)

    if not user.is_owner:
        if user.division:
            invoice_qs = invoice_qs.filter(customer__division=user.division.name)
            payment_qs = payment_qs.filter(invoice__customer__division=user.division.name)
            customer_qs = customer_qs.filter(division=user.division.name)
        else:
            invoice_qs = invoice_qs.none()
            payment_qs = payment_qs.none()
            customer_qs = customer_qs.none()

    # Date ranges
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    this_year_start = today.replace(month=1, day=1)

    # Revenue metrics
    total_revenue = payment_qs.aggregate(total=Sum('amount'))['total'] or 0
    month_revenue = payment_qs.filter(date__gte=this_month_start).aggregate(total=Sum('amount'))['total'] or 0
    last_month_revenue = payment_qs.filter(date__gte=last_month_start, date__lt=this_month_start).aggregate(total=Sum('amount'))['total'] or 0

    # Outstanding AR
    outstanding_invoices = invoice_qs.filter(status__in=['sent', 'overdue'])
    total_outstanding = sum(inv.balance_due for inv in outstanding_invoices)
    overdue_count = invoice_qs.filter(status='overdue').count()

    # Invoice counts by status
    status_counts = {}
    for status, label in Invoice.STATUS_CHOICES:
        status_counts[status] = invoice_qs.filter(status=status).count()

    # Revenue by division (owner only)
    revenue_by_division = []
    if user.is_owner:
        for div in Division.objects.all():
            div_revenue = Payment.objects.filter(
                invoice__customer__division=div.name
            ).aggregate(total=Sum('amount'))['total'] or 0
            revenue_by_division.append({'division': div, 'revenue': div_revenue})

    # Monthly revenue for chart (last 6 months)
    monthly_revenue = []
    max_rev = 0
    for i in range(5, -1, -1):
        month_start = (today.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        if i == 0:
            month_end = today + timedelta(days=1)
        else:
            month_end = (month_start + timedelta(days=32)).replace(day=1)
        month_total = payment_qs.filter(date__gte=month_start, date__lt=month_end).aggregate(total=Sum('amount'))['total'] or 0
        monthly_revenue.append({
            'month': month_start.strftime('%b %Y'),
            'revenue': month_total,
        })
        if month_total > max_rev:
            max_rev = month_total

    # Calculate bar heights (max 120px)
    for m in monthly_revenue:
        m['bar_height'] = int((m['revenue'] / max_rev) * 120) if max_rev > 0 else 4

    context = {
        'total_revenue': total_revenue,
        'month_revenue': month_revenue,
        'last_month_revenue': last_month_revenue,
        'total_outstanding': total_outstanding,
        'overdue_count': overdue_count,
        'total_customers': customer_qs.count(),
        'status_counts': status_counts,
        'revenue_by_division': revenue_by_division,
        'monthly_revenue': monthly_revenue,
        'divisions': divisions,
    }
    return render(request, 'reporting/reports.html', context)
