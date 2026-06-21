"""Views for invoicing — CRUD, PDF generation, payment recording."""
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, F
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from core.models import Customer, Invoice, InvoiceLineItem, Payment
from core.views import DivisionMixin
from invoicing.forms import InvoiceForm, InvoiceLineFormSet, PaymentForm


class InvoiceListView(LoginRequiredMixin, DivisionMixin, ListView):
    model = Invoice
    template_name = 'invoicing/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset().select_related('customer')
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        search = self.request.GET.get('q')
        if search:
            qs = qs.filter(
                Q(invoice_number__icontains=search) |
                Q(customer__name__icontains=search)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['status_filter'] = self.request.GET.get('status', '')
        ctx['search'] = self.request.GET.get('q', '')
        ctx['status_choices'] = Invoice.STATUS_CHOICES
        return ctx


class InvoiceCreateView(LoginRequiredMixin, CreateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoicing/invoice_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['line_formset'] = InvoiceLineFormSet(self.request.POST)
        else:
            ctx['line_formset'] = InvoiceLineFormSet()
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        line_formset = ctx['line_formset']
        if line_formset.is_valid():
            form.instance.created_by = self.request.user
            self.object = form.save()
            line_formset.instance = self.object
            line_formset.save()
            messages.success(self.request, f"Invoice #{self.object.invoice_number} created.")
            return redirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('invoice-detail', kwargs={'pk': self.object.pk})


class InvoiceDetailView(LoginRequiredMixin, DivisionMixin, DetailView):
    model = Invoice
    template_name = 'invoicing/invoice_detail.html'
    context_object_name = 'invoice'

    def get_queryset(self):
        return super().get_queryset().select_related('customer', 'created_by').prefetch_related('lines', 'payments')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['payment_form'] = PaymentForm()
        return ctx


class InvoiceUpdateView(LoginRequiredMixin, DivisionMixin, UpdateView):
    model = Invoice
    form_class = InvoiceForm
    template_name = 'invoicing/invoice_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['line_formset'] = InvoiceLineFormSet(self.request.POST, instance=self.object)
        else:
            ctx['line_formset'] = InvoiceLineFormSet(instance=self.object)
        return ctx

    def form_valid(self, form):
        ctx = self.get_context_data()
        line_formset = ctx['line_formset']
        if line_formset.is_valid():
            self.object = form.save()
            line_formset.save()
            messages.success(self.request, f"Invoice #{self.object.invoice_number} updated.")
            return redirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('invoice-detail', kwargs={'pk': self.object.pk})


@login_required
@require_POST
def invoice_add_payment(request, pk):
    """Record a payment against an invoice."""
    invoice = get_object_or_404(Invoice, pk=pk)
    if not request.user.is_owner and invoice.customer.division != request.user.division.name:
        messages.error(request, "Access denied.")
        return redirect('invoice-list')

    form = PaymentForm(request.POST)
    if form.is_valid():
        payment = form.save(commit=False)
        payment.invoice = invoice
        payment.recorded_by = request.user
        payment.save()
        messages.success(request, f"Payment of ${payment.amount} recorded.")
    else:
        messages.error(request, "Invalid payment data.")
    return redirect('invoice-detail', pk=pk)


@login_required
@require_POST
def invoice_update_status(request, pk):
    """Update invoice status."""
    invoice = get_object_or_404(Invoice, pk=pk)
    if not request.user.is_owner and invoice.customer.division != request.user.division.name:
        messages.error(request, "Access denied.")
        return redirect('invoice-list')

    status = request.POST.get('status')
    if status in dict(Invoice.STATUS_CHOICES):
        invoice.status = status
        invoice.save()
        messages.success(request, f"Invoice status updated to {invoice.get_status_display()}.")
    return redirect('invoice-detail', pk=pk)


@login_required
def invoice_pdf(request, pk):
    """Generate PDF invoice."""
    invoice = get_object_or_404(
        Invoice.objects.select_related('customer', 'created_by').prefetch_related('lines', 'payments'),
        pk=pk
    )
    if not request.user.is_owner and invoice.customer.division != request.user.division.name:
        messages.error(request, "Access denied.")
        return redirect('invoice-list')

    html_string = render_to_string('invoicing/invoice_pdf.html', {
        'invoice': invoice,
        'company_name': 'Alexander AI Solutions',
        'company_phone': '',
        'company_email': '',
    })

    try:
        from weasyprint import HTML
        pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
        return response
    except Exception as e:
        # Fallback: return HTML if WeasyPrint system deps not available
        return HttpResponse(html_string, content_type='text/html')


@login_required
def api_invoices(request):
    """API endpoint for offline sync."""
    user = request.user
    invoices = Invoice.objects.select_related('customer').prefetch_related('lines', 'payments')
    if not user.is_owner:
        if user.division:
            invoices = invoices.filter(customer__division=user.division.name)
        else:
            invoices = invoices.none()

    data = []
    for inv in invoices.order_by('-updated_at')[:500]:
        data.append({
            'id': inv.id,
            'invoice_number': inv.invoice_number,
            'customer_id': inv.customer_id,
            'customer_name': inv.customer.name,
            'status': inv.status,
            'issue_date': inv.issue_date.isoformat(),
            'due_date': inv.due_date.isoformat(),
            'tax_rate': str(inv.tax_rate),
            'subtotal': str(inv.subtotal),
            'tax_amount': str(inv.tax_amount),
            'total_amount': str(inv.total_amount),
            'amount_paid': str(inv.amount_paid),
            'balance_due': str(inv.balance_due),
            'notes': inv.notes,
            'lines': [
                {
                    'description': line.description,
                    'quantity': str(line.quantity),
                    'rate': str(line.rate),
                    'amount': str(line.amount),
                }
                for line in inv.lines.all()
            ],
            'payments': [
                {
                    'amount': str(p.amount),
                    'date': p.date.isoformat(),
                    'method': p.method,
                    'reference': p.reference,
                }
                for p in inv.payments.all()
            ],
        })
    return JsonResponse({'invoices': data})


@login_required
def api_customers(request):
    """API endpoint for offline sync."""
    user = request.user
    customers = Customer.objects.filter(is_active=True)
    if not user.is_owner:
        if user.division:
            customers = customers.filter(division=user.division.name)
        else:
            customers = customers.none()

    data = []
    for c in customers.order_by('name'):
        data.append({
            'id': c.id,
            'name': c.name,
            'company': c.company,
            'division': c.division,
            'address': c.address,
            'phone': c.phone,
            'email': c.email,
            'notes': c.notes,
        })
    return JsonResponse({'customers': data})
