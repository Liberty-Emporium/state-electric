"""
Views for the standard app: Jobs, Time Tracking, Payroll, Estimates.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from core.models import Customer, Division, User, Invoice, InvoiceLineItem
from core.views import DivisionMixin
from .forms import (
    JobForm, TimeEntryForm, PayPeriodForm, PayrollEntryForm,
    EstimateForm, EstimateLineFormSet,
)
from .models import (
    Job, TimeEntry, PayPeriod, PayrollEntry,
    Estimate, EstimateLineItem,
)


# ─── JOBS ──────────────────────────────────────────────────────────

class JobListView(LoginRequiredMixin, DivisionMixin, ListView):
    model = Job
    template_name = 'standard/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related('customer', 'division', 'created_by')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        search = self.request.GET.get('q')
        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(customer__name__icontains=search)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_filter'] = self.request.GET.get('status', '')
        ctx['search'] = self.request.GET.get('q', '')
        ctx['status_choices'] = Job.STATUS_CHOICES
        return ctx


class JobCreateView(LoginRequiredMixin, CreateView):
    model = Job
    form_class = JobForm
    template_name = 'standard/job_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        if not form.instance.division_id:
            form.instance.division = self.request.user.division
        messages.success(self.request, f"Job '{form.instance.title}' created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('job-detail', kwargs={'pk': self.object.pk})


class JobDetailView(LoginRequiredMixin, DivisionMixin, DetailView):
    model = Job
    template_name = 'standard/job_detail.html'
    context_object_name = 'job'

    def get_queryset(self):
        return super().get_queryset().select_related('customer', 'division', 'created_by').prefetch_related('time_entries')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['time_entries'] = self.object.time_entries.all()[:20]
        return ctx


class JobUpdateView(LoginRequiredMixin, DivisionMixin, UpdateView):
    model = Job
    form_class = JobForm
    template_name = 'standard/job_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f"Job '{form.instance.title}' updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('job-detail', kwargs={'pk': self.object.pk})


@login_required
@require_POST
def job_update_status(request, pk):
    job = get_object_or_404(Job, pk=pk)
    status = request.POST.get('status')
    if status in dict(Job.STATUS_CHOICES):
        job.status = status
        if status == 'completed':
            job.completed_date = timezone.now().date()
        job.save()
        messages.success(self.request, f"Job status updated to {job.get_status_display()}.")
    return redirect('job-detail', pk=pk)


# ─── TIME TRACKING ────────────────────────────────────────────────

class TimeEntryListView(LoginRequiredMixin, ListView):
    model = TimeEntry
    template_name = 'standard/time_list.html'
    context_object_name = 'entries'
    paginate_by = 50

    def get_queryset(self):
        qs = TimeEntry.objects.select_related('employee', 'job')
        if not self.request.user.is_superuser:
            if self.request.user.division:
                qs = qs.filter(job__division=self.request.user.division)
        employee = self.request.GET.get('employee')
        if employee:
            qs = qs.filter(employee_id=employee)
        date_from = self.request.GET.get('from')
        if date_from:
            qs = qs.filter(date__gte=date_from)
        date_to = self.request.GET.get('to')
        if date_to:
            qs = qs.filter(date__lte=date_to)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['total_hours'] = self.get_queryset().aggregate(t=Sum('hours'))['t'] or 0
        # Active jobs for clock-in dropdown
        from standard.models import Job
        active_jobs = Job.objects.filter(status__in=['scheduled', 'in_progress'])
        if not self.request.user.is_superuser and self.request.user.division:
            active_jobs = active_jobs.filter(division=self.request.user.division)
        ctx['active_jobs'] = active_jobs
        # Active (open) time entries for clock-out
        ctx['active_entries'] = TimeEntry.objects.filter(
            employee=self.request.user, clock_out__isnull=True
        ).select_related('job')
        return ctx


class TimeEntryCreateView(LoginRequiredMixin, CreateView):
    model = TimeEntry
    form_class = TimeEntryForm
    template_name = 'standard/time_form.html'

    def form_valid(self, form):
        messages.success(self.request, "Time entry recorded.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('time-list')


class TimeEntryUpdateView(LoginRequiredMixin, UpdateView):
    model = TimeEntry
    form_class = TimeEntryForm
    template_name = 'standard/time_form.html'

    def get_success_url(self):
        return reverse_lazy('time-list')


@login_required
@require_POST
def clock_in(request):
    """Clock in to a job."""
    job_id = request.POST.get('job_id')
    job = get_object_or_404(Job, pk=job_id)
    existing = TimeEntry.objects.filter(
        employee=request.user, job=job,
        clock_in__isnull=False, clock_out__isnull=True
    ).first()
    if existing:
        messages.error(request, "You're already clocked in to this job.")
    else:
        entry = TimeEntry.objects.create(
            employee=request.user,
            job=job,
            date=timezone.now().date(),
            clock_in=timezone.now(),
            hours=0,
        )
        messages.success(self.request, f"Clocked in to '{job.title}' at {entry.clock_in.strftime('%H:%M')}.")
    return redirect('time-list')


@login_required
@require_POST
def clock_out(request):
    """Clock out from a job."""
    entry_id = request.POST.get('entry_id')
    entry = get_object_or_404(TimeEntry, pk=entry_id, employee=request.user)
    entry.clock_out = timezone.now()
    delta = entry.clock_out - entry.clock_in
    entry.hours = round(delta.total_seconds() / 3600, 2)
    entry.save()
    messages.success(self.request, f"Clocked out. Total: {entry.hours} hours.")
    return redirect('time-list')


# ─── PAYROLL ───────────────────────────────────────────────────────

class PayPeriodListView(LoginRequiredMixin, ListView):
    model = PayPeriod
    template_name = 'standard/payperiod_list.html'
    context_object_name = 'pay_periods'

    def get_queryset(self):
        qs = PayPeriod.objects.select_related('division').prefetch_related('payroll_entries')
        if not self.request.user.is_superuser and self.request.user.division:
            qs = qs.filter(division=self.request.user.division)
        return qs


class PayPeriodCreateView(LoginRequiredMixin, CreateView):
    model = PayPeriod
    form_class = PayPeriodForm
    template_name = 'standard/payperiod_form.html'

    def form_valid(self, form):
        messages.success(self.request, "Pay period created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('payperiod-detail', kwargs={'pk': self.object.pk})


class PayPeriodDetailView(LoginRequiredMixin, DetailView):
    model = PayPeriod
    template_name = 'standard/payperiod_detail.html'
    context_object_name = 'pay_period'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['entries'] = self.object.payroll_entries.select_related('employee').all()
        return ctx


@login_required
@require_POST
def payroll_calculate(request, pk):
    """Calculate payroll for all entries in a pay period."""
    pay_period = get_object_or_404(PayPeriod, pk=pk)
    entries = pay_period.payroll_entries.all()
    for entry in entries:
        if entry.gross_pay and not entry.net_pay:
            entry.calculate_taxes()
            entry.save()
    messages.success(self.request, f"Calculated payroll for {entries.count()} employees.")
    return redirect('payperiod-detail', pk=pk)


@login_required
def payroll_entry_edit(request, pk, entry_pk):
    """Edit a payroll entry."""
    pay_period = get_object_or_404(PayPeriod, pk=pk)
    entry = get_object_or_404(PayrollEntry, pk=entry_pk, pay_period=pay_period)
    if request.method == 'POST':
        form = PayrollEntryForm(request.POST, instance=entry)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.calculate_taxes()
            entry.save()
            messages.success(self.request, "Payroll entry updated.")
            return redirect('payperiod-detail', pk=pk)
    else:
        form = PayrollEntryForm(instance=entry)
    return render(request, 'standard/payrollentry_form.html', {
        'form': form, 'pay_period': pay_period, 'entry': entry,
    })


@login_required
def pay_stub_pdf(request, pk, entry_pk):
    """Generate pay stub PDF."""
    pay_period = get_object_or_404(PayPeriod, pk=pk)
    entry = get_object_or_404(PayrollEntry, pk=entry_pk, pay_period=pay_period)
    html_string = render_to_string('standard/paystub_pdf.html', {
        'entry': entry,
        'pay_period': pay_period,
        'company_name': 'State Electric',
    })
    try:
        from weasyprint import HTML
        pdf = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="paystub_{entry.employee.username}_{pay_period.start_date}.pdf"'
        return response
    except Exception:
        return HttpResponse(html_string, content_type='text/html')


# ─── ESTIMATES ────────────────────────────────────────────────────

class EstimateListView(LoginRequiredMixin, DivisionMixin, ListView):
    model = Estimate
    template_name = 'standard/estimate_list.html'
    context_object_name = 'estimates'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related('customer', 'division')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        search = self.request.GET.get('q')
        if search:
            qs = qs.filter(
                Q(estimate_number__icontains=search) |
                Q(customer__name__icontains=search)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_filter'] = self.request.GET.get('status', '')
        ctx['search'] = self.request.GET.get('q', '')
        ctx['status_choices'] = Estimate.STATUS_CHOICES
        return ctx


class EstimateCreateView(LoginRequiredMixin, CreateView):
    model = Estimate
    form_class = EstimateForm
    template_name = 'standard/estimate_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['line_formset'] = EstimateLineFormSet(self.request.POST)
        else:
            ctx['line_formset'] = EstimateLineFormSet()
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        line_formset = ctx['line_formset']
        if line_formset.is_valid():
            if not form.instance.division_id:
                form.instance.division = self.request.user.division
            form.instance.created_by = self.request.user
            self.object = form.save()
            line_formset.instance = self.object
            line_formset.save()
            messages.success(self.request, f"Estimate #{self.object.estimate_number} created.")
            return redirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('estimate-detail', kwargs={'pk': self.object.pk})


class EstimateDetailView(LoginRequiredMixin, DivisionMixin, DetailView):
    model = Estimate
    template_name = 'standard/estimate_detail.html'
    context_object_name = 'estimate'

    def get_queryset(self):
        return super().get_queryset().select_related('customer', 'division', 'created_by').prefetch_related('lines')


class EstimateUpdateView(LoginRequiredMixin, DivisionMixin, UpdateView):
    model = Estimate
    form_class = EstimateForm
    template_name = 'standard/estimate_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['line_formset'] = EstimateLineFormSet(self.request.POST, instance=self.object)
        else:
            ctx['line_formset'] = EstimateLineFormSet(instance=self.object)
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        line_formset = ctx['line_formset']
        if line_formset.is_valid():
            self.object = form.save()
            line_formset.save()
            messages.success(self.request, f"Estimate #{self.object.estimate_number} updated.")
            return redirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('estimate-detail', kwargs={'pk': self.object.pk})


@login_required
@require_POST
def estimate_convert_to_invoice(request, pk):
    """Convert an accepted estimate into an invoice."""
    estimate = get_object_or_404(Estimate, pk=pk)
    if estimate.status != 'accepted':
        messages.error(self.request, "Estimate must be accepted before converting.")
        return redirect('estimate-detail', pk=pk)

    invoice = Invoice.objects.create(
        customer=estimate.customer,
        status='draft',
        tax_rate=estimate.tax_rate,
        notes=f"Converted from Estimate #{estimate.estimate_number}",
        created_by=request.user,
    )
    for line in estimate.lines.all():
        InvoiceLineItem.objects.create(
            invoice=invoice,
            description=line.description,
            quantity=line.quantity,
            rate=line.rate,
            sort_order=line.sort_order,
        )
    estimate.status = 'converted'
    estimate.converted_invoice_id = invoice.pk
    estimate.save()
    messages.success(self.request, f"Estimate converted to Invoice #{invoice.invoice_number}.")
    return redirect('invoice-detail', pk=invoice.pk)


# ─── API for offline sync ─────────────────────────────────────────

@login_required
def api_jobs(request):
    """API endpoint for offline sync of jobs."""
    user = request.user
    jobs = Job.objects.select_related('customer', 'division')
    if not user.is_superuser and user.division:
        jobs = jobs.filter(division=user.division)
    data = [{
        'id': j.id,
        'title': j.title,
        'customer': j.customer.name,
        'status': j.status,
        'priority': j.priority,
        'scheduled_date': str(j.scheduled_date) if j.scheduled_date else None,
    } for j in jobs]
    return JsonResponse({'jobs': data})
