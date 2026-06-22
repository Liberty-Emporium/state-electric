"""
State Electric — Views
Dashboard, Customer management, with division-based filtering.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum, Count, F
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from core.models import Customer, Division, Invoice, Payment, User
from invoicing.forms import CustomerForm, InvoiceForm, InvoiceLineFormSet, PaymentForm


def get_user_divisions(user):
    """Get divisions the user can see."""
    if user.is_owner:
        return Division.objects.all()
    if user.division:
        return Division.objects.filter(pk=user.division.pk)
    return Division.objects.none()


def get_division_filter(user, queryset, division_field='division'):
    """Filter queryset by user's division access."""
    if user.is_owner:
        return queryset
    if user.division:
        return queryset.filter(**{division_field: user.division.name if hasattr(user.division, 'name') else user.division})
    return queryset.none()


class DivisionMixin:
    """Mixin to filter querysets by user's division."""
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_owner:
            return qs
        if user.division:
            return qs.filter(division=user.division.name)
        return qs.none()


@login_required
def dashboard(request):
    """Main dashboard with revenue summary."""
    user = request.user
    divisions = get_user_divisions(user)

    # Base invoice query filtered by division
    invoice_qs = Invoice.objects.all()
    customer_qs = Customer.objects.filter(is_active=True)
    if not user.is_owner:
        if user.division:
            invoice_qs = invoice_qs.filter(customer__division=user.division.name)
            customer_qs = customer_qs.filter(division=user.division.name)
        else:
            invoice_qs = invoice_qs.none()
            customer_qs = customer_qs.none()

    # Stats
    total_revenue = invoice_qs.filter(status='paid').aggregate(
        total=Sum('payments__amount')
    )['total'] or 0

    # Calculate outstanding: sum of line items minus payments
    try:
        outstanding_invoices = invoice_qs.filter(status__in=['sent', 'overdue'])
        outstanding = 0
        for inv in outstanding_invoices:
            inv_total = sum(line.quantity * line.rate for line in inv.lines.all()) * (1 + inv.tax_rate)
            paid_total = sum(p.amount for p in inv.payments.all())
            outstanding += (inv_total - paid_total)
    except Exception:
        outstanding = 0

    overdue_count = invoice_qs.filter(status='overdue').count()
    total_customers = customer_qs.count()

    # Revenue by division (owner sees all)
    revenue_by_division = []
    if user.is_owner:
        for div in Division.objects.all():
            div_revenue = Invoice.objects.filter(
                customer__division=div.name, status='paid'
            ).aggregate(total=Sum('payments__amount'))['total'] or 0
            revenue_by_division.append({'division': div, 'revenue': div_revenue})

    # Recent invoices
    recent_invoices = invoice_qs.select_related('customer').order_by('-created_at')[:10]

    # Standard tier stats
    from standard.models import Job, Estimate
    active_jobs = Job.objects.filter(status__in=['scheduled', 'in_progress'])
    pending_estimates = Estimate.objects.filter(status__in=['draft', 'sent'])
    if not user.is_owner:
        if user.division:
            active_jobs = active_jobs.filter(division=user.division)
            pending_estimates = pending_estimates.filter(division=user.division)

    context = {
        'total_revenue': total_revenue,
        'outstanding': outstanding,
        'overdue_count': overdue_count,
        'total_customers': total_customers,
        'revenue_by_division': revenue_by_division,
        'recent_invoices': recent_invoices,
        'divisions': divisions,
        'active_jobs': active_jobs.count(),
        'pending_estimates': pending_estimates.count(),
    }
    try:
        from premium.models import RecurringInvoice
        ctx['active_recurring'] = RecurringInvoice.objects.filter(status='active').count()
    except Exception:
        ctx['active_recurring'] = 0
    return render(request, 'core/dashboard.html', context)


# ═══ CUSTOMER VIEWS ═══

class CustomerListView(LoginRequiredMixin, DivisionMixin, ListView):
    model = Customer
    template_name = 'core/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().filter(is_active=True)
        search = self.request.GET.get('q')
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(company__icontains=search) | Q(phone__icontains=search))
        division = self.request.GET.get('division')
        if division:
            qs = qs.filter(division=division)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['search'] = self.request.GET.get('q', '')
        ctx['filter_division'] = self.request.GET.get('division', '')
        return ctx


class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'core/customer_form.html'
    success_url = reverse_lazy('customer-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"Customer '{form.instance.name}' created.")
        return super().form_valid(form)


class CustomerUpdateView(LoginRequiredMixin, DivisionMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'core/customer_form.html'
    success_url = reverse_lazy('customer-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"Customer '{form.instance.name}' updated.")
        return super().form_valid(form)


class CustomerDetailView(LoginRequiredMixin, DivisionMixin, DetailView):
    model = Customer
    template_name = 'core/customer_detail.html'
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['invoices'] = self.object.invoices.select_related('customer').order_by('-created_at')[:20]
        return ctx


@login_required
@require_POST
def customer_delete(request, pk):
    """Soft-delete a customer."""
    customer = get_object_or_404(Customer, pk=pk)
    if not request.user.is_owner and customer.division != request.user.division.name:
        messages.error(request, "You can only delete customers in your division.")
        return redirect('customer-list')
    customer.is_active = False
    customer.save()
    messages.success(request, f"Customer '{customer.name}' deactivated.")
    return redirect('customer-list')
