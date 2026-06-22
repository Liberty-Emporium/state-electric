"""
Views for the premium app: Recurring Invoices, Expenses, Bank Reconciliation,
Purchase Orders, 1099 Support, Tax Forms, Data Import, Contracts, AI Estimates.
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

from core.models import Customer, Division, User
from core.views import DivisionMixin
from invoicing.models import Invoice, InvoiceLineItem
from standard.models import Job, Estimate, EstimateLineItem
from .forms import (
    RecurringInvoiceForm, RecurringLineFormSet,
    ExpenseForm, BankAccountForm, BankTransactionForm,
    PurchaseOrderForm, POLineFormSet,
    ContractorForm, ContractorPaymentForm,
    TaxFormForm, DataImportForm, ContractForm, EstimateTemplateForm,
)
from .models import (
    RecurringInvoice, Expense, ExpenseCategory,
    BankAccount, BankTransaction,
    PurchaseOrder, Contractor, ContractorPayment,
    TaxForm, DataImport, Contract, EstimateTemplate,
)


# ═══════════════════════════════════════════════════════════════════
# RECURRING INVOICES
# ═══════════════════════════════════════════════════════════════════

class RecurringInvoiceListView(LoginRequiredMixin, ListView):
    model = RecurringInvoice
    template_name = 'premium/recurring_list.html'
    context_object_name = 'recurrings'

    def get_queryset(self):
        qs = RecurringInvoice.objects.select_related('customer', 'division')
        if not self.request.user.is_superuser and self.request.user.division:
            qs = qs.filter(division=self.request.user.division)
        return qs


class RecurringInvoiceCreateView(LoginRequiredMixin, CreateView):
    model = RecurringInvoice
    form_class = RecurringInvoiceForm
    template_name = 'premium/recurring_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['line_formset'] = RecurringLineFormSet(self.request.POST)
        else:
            ctx['line_formset'] = RecurringLineFormSet()
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
            messages.success(self.request, f"Recurring invoice created for {self.object.customer.name}.")
            return redirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('recurring-list')


class RecurringInvoiceDetailView(LoginRequiredMixin, DetailView):
    model = RecurringInvoice
    template_name = 'premium/recurring_detail.html'
    context_object_name = 'recurring'


@login_required
@require_POST
def recurring_generate_now(request, pk):
    """Generate an invoice from a recurring template right now."""
    recurring = get_object_or_404(RecurringInvoice, pk=pk)
    invoice = Invoice.objects.create(
        customer=recurring.customer,
        status='draft',
        tax_rate=recurring.tax_rate,
        notes=f"Generated from recurring template",
        created_by=request.user,
    )
    for line in recurring.lines.all():
        InvoiceLineItem.objects.create(
            invoice=invoice,
            description=line.description,
            quantity=line.quantity,
            rate=line.rate,
            sort_order=line.sort_order,
        )
    # Update next invoice date
    from datetime import timedelta
    freq_map = {
        'weekly': timedelta(weeks=1),
        'biweekly': timedelta(weeks=2),
        'monthly': timedelta(days=30),
        'quarterly': timedelta(days=90),
        'annually': timedelta(days=365),
    }
    recurring.next_invoice_date = recurring.next_invoice_date + freq_map.get(recurring.frequency, timedelta(days=30))
    recurring.save()
    messages.success(self.request, f"Invoice #{invoice.invoice_number} generated from recurring template.")
    return redirect('invoice-detail', pk=invoice.pk)


# ═══════════════════════════════════════════════════════════════════
# EXPENSES
# ═══════════════════════════════════════════════════════════════════

class ExpenseListView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = 'premium/expense_list.html'
    context_object_name = 'expenses'
    paginate_by = 50

    def get_queryset(self):
        qs = Expense.objects.select_related('category', 'job', 'division')
        if not self.request.user.is_superuser and self.request.user.division:
            qs = qs.filter(division=self.request.user.division)
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_queryset()
        ctx['total_amount'] = qs.aggregate(t=Sum('amount'))['t'] or 0
        ctx['status_filter'] = self.request.GET.get('status', '')
        return ctx


class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'premium/expense_form.html'

    def form_valid(self, form):
        if not form.instance.division_id:
            form.instance.division = self.request.user.division
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Expense '{form.instance.description}' recorded.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('expense-list')


class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'premium/expense_form.html'

    def get_success_url(self):
        return reverse_lazy('expense-list')


# ═══════════════════════════════════════════════════════════════════
# BANK RECONCILIATION
# ═══════════════════════════════════════════════════════════════════

class BankAccountListView(LoginRequiredMixin, ListView):
    model = BankAccount
    template_name = 'premium/bank_list.html'
    context_object_name = 'accounts'

    def get_queryset(self):
        qs = BankAccount.objects.filter(is_active=True)
        if not self.request.user.is_superuser and self.request.user.division:
            qs = qs.filter(division=self.request.user.division)
        return qs


class BankAccountCreateView(LoginRequiredMixin, CreateView):
    model = BankAccount
    form_class = BankAccountForm
    template_name = 'premium/bank_form.html'

    def get_success_url(self):
        return reverse_lazy('bank-list')


class BankReconciliationView(LoginRequiredMixin, DetailView):
    model = BankAccount
    template_name = 'premium/bank_reconcile.html'
    context_object_name = 'account'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['unmatched'] = self.object.transactions.filter(status='unmatched').order_by('-date')[:50]
        return ctx


@login_required
@require_POST
def bank_import_csv(request, pk):
    """Import bank transactions from CSV."""
    account = get_object_or_404(BankAccount, pk=pk)
    csv_file = request.FILES.get('csv_file')
    if not csv_file:
        messages.error(request, "No file uploaded.")
        return redirect('bank-reconcile', pk=pk)

    import csv
    from io import StringIO
    decoded = csv_file.read().decode('utf-8-sig')
    reader = csv.DictReader(StringIO(decoded))
    created = 0
    for row in reader:
        try:
            BankTransaction.objects.create(
                bank_account=account,
                date=row.get('date', row.get('Date', '')),
                description=row.get('description', row.get('Description', row.get('Payee', ''))),
                amount=row.get('amount', row.get('Amount', 0)),
                reference=row.get('reference', row.get('Reference', row.get('Ref', ''))),
            )
            created += 1
        except Exception:
            pass
    messages.success(request, f"Imported {created} transactions.")
    return redirect('bank-reconcile', pk=pk)


@login_required
@require_POST
def bank_match_transaction(request, pk):
    """Match a bank transaction to a payment or expense."""
    transaction = get_object_or_404(BankTransaction, pk=pk)
    match_type = request.POST.get('match_type')
    match_id = request.POST.get('match_id')

    if match_type == 'payment':
        from invoicing.models import Payment
        transaction.matched_payment = get_object_or_404(Payment, pk=match_id)
        transaction.status = 'matched'
    elif match_type == 'expense':
        transaction.matched_expense = get_object_or_404(Expense, pk=match_id)
        transaction.status = 'matched'
    transaction.save()
    messages.success(self.request, "Transaction matched.")
    return redirect('bank-reconcile', pk=transaction.bank_account.pk)


# ═══════════════════════════════════════════════════════════════════
# PURCHASE ORDERS
# ═══════════════════════════════════════════════════════════════════

class PurchaseOrderListView(LoginRequiredMixin, ListView):
    model = PurchaseOrder
    template_name = 'premium/po_list.html'
    context_object_name = 'pos'

    def get_queryset(self):
        qs = PurchaseOrder.objects.select_related('division', 'job')
        if not self.request.user.is_superuser and self.request.user.division:
            qs = qs.filter(division=self.request.user.division)
        return qs


class PurchaseOrderCreateView(LoginRequiredMixin, CreateView):
    model = PurchaseOrder
    form_class = PurchaseOrderForm
    template_name = 'premium/po_form.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        if self.request.POST:
            ctx['line_formset'] = POLineFormSet(self.request.POST)
        else:
            ctx['line_formset'] = POLineFormSet()
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
            messages.success(self.request, f"Purchase Order #{self.object.po_number} created.")
            return redirect(self.get_success_url())
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('po-detail', kwargs={'pk': self.object.pk})


class PurchaseOrderDetailView(LoginRequiredMixin, DetailView):
    model = PurchaseOrder
    template_name = 'premium/po_detail.html'
    context_object_name = 'po'


# ═══════════════════════════════════════════════════════════════════
# 1099 CONTRACTORS
# ═══════════════════════════════════════════════════════════════════

class ContractorListView(LoginRequiredMixin, ListView):
    model = Contractor
    template_name = 'premium/contractor_list.html'
    context_object_name = 'contractors'

    def get_queryset(self):
        return Contractor.objects.filter(is_active=True)


class ContractorCreateView(LoginRequiredMixin, CreateView):
    model = Contractor
    form_class = ContractorForm
    template_name = 'premium/contractor_form.html'
    success_url = reverse_lazy('contractor-list')


class ContractorUpdateView(LoginRequiredMixin, UpdateView):
    model = Contractor
    form_class = ContractorForm
    template_name = 'premium/contractor_form.html'
    success_url = reverse_lazy('contractor-list')


class ContractorPaymentCreateView(LoginRequiredMixin, CreateView):
    model = ContractorPayment
    form_class = ContractorPaymentForm
    template_name = 'premium/contractor_payment_form.html'

    def form_valid(self, form):
        if not form.instance.division_id:
            form.instance.division = self.request.user.division
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Payment to {form.instance.contractor.name} recorded.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('contractor-list')


@login_required
def generate_1099(request, contractor_pk, year):
    """Generate 1099-NEC form for a contractor."""
    contractor = get_object_or_404(Contractor, pk=contractor_pk)
    payments = ContractorPayment.objects.filter(
        contractor=contractor, date__year=year, is_1099_reportable=True
    )
    total = payments.aggregate(t=Sum('amount'))['t'] or 0

    tax_form, created = TaxForm.objects.get_or_create(
        form_type='1099_nec', tax_year=year, recipient_name=contractor.name,
        defaults={
            'recipient_tax_id': contractor.tax_id,
            'recipient_address': contractor.address,
            'total_compensation': total,
        }
    )
    if not created:
        tax_form.total_compensation = total
        tax_form.save()

    messages.success(self.request, f"1099-NEC generated for {contractor.name} ({year}) — ${total}")
    return redirect('tax-form-detail', pk=tax_form.pk)


# ═══════════════════════════════════════════════════════════════════
# TAX FORMS
# ═══════════════════════════════════════════════════════════════════

class TaxFormListView(LoginRequiredMixin, ListView):
    model = TaxForm
    template_name = 'premium/taxform_list.html'
    context_object_name = 'tax_forms'

    def get_queryset(self):
        return TaxForm.objects.all()


class TaxFormDetailView(LoginRequiredMixin, DetailView):
    model = TaxForm
    template_name = 'premium/taxform_detail.html'
    context_object_name = 'tax_form'


@login_required
def tax_form_pdf(request, pk):
    """Generate PDF of tax form."""
    tax_form = get_object_or_404(TaxForm, pk=pk)
    html_string = render_to_string('premium/taxform_pdf.html', {'tax_form': tax_form})
    try:
        from weasyprint import HTML
        pdf = HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{tax_form.get_form_type_display()}_{tax_form.recipient_name}_{tax_form.tax_year}.pdf"'
        return response
    except Exception:
        return HttpResponse(html_string, content_type='text/html')


# ═══════════════════════════════════════════════════════════════════
# DATA IMPORT
# ═══════════════════════════════════════════════════════════════════

class DataImportListView(LoginRequiredMixin, ListView):
    model = DataImport
    template_name = 'premium/import_list.html'
    context_object_name = 'imports'

    def get_queryset(self):
        return DataImport.objects.all()


class DataImportCreateView(LoginRequiredMixin, CreateView):
    model = DataImport
    form_class = DataImportForm
    template_name = 'premium/import_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        self.object = form.save()
        # Process the import
        self.process_import(self.object)
        messages.success(self.request, f"Import completed: {self.object.imported_rows} rows imported, {self.object.error_rows} errors.")
        return redirect('import-list')

    def process_import(self, data_import):
        """Process the uploaded file."""
        import csv
        from io import StringIO
        from datetime import datetime
        from decimal import Decimal, InvalidOperation

        data_import.status = 'processing'
        data_import.started_at = timezone.now()
        data_import.save()

        try:
            file_content = data_import.file.read().decode('utf-8-sig')
            reader = csv.DictReader(StringIO(file_content))
            rows = list(reader)
            data_import.total_rows = len(rows)

            imported = 0
            errors = 0
            error_log = []

            if data_import.import_type in ('customers', 'all'):
                for i, row in enumerate(rows):
                    try:
                        name = row.get('Name', row.get('name', row.get('Customer', ''))).strip()
                        if not name:
                            continue
                        Customer.objects.update_or_create(
                            name=name,
                            defaults={
                                'company': row.get('Company', row.get('company', '')).strip(),
                                'address': row.get('Address', row.get('address', '')).strip(),
                                'phone': row.get('Phone', row.get('phone', '')).strip(),
                                'email': row.get('Email', row.get('email', '')).strip(),
                                'division': row.get('Division', row.get('division', 'commercial')).strip(),
                                'is_active': True,
                            }
                        )
                        imported += 1
                    except Exception as e:
                        errors += 1
                        error_log.append(f"Row {i+2}: {e}")

            elif data_import.import_type in ('invoices', 'all'):
                invoices = {}
                for row in rows:
                    inv_num = row.get('InvoiceNumber', row.get('Invoice #', row.get('Num', ''))).strip()
                    if not inv_num:
                        continue
                    if inv_num not in invoices:
                        invoices[inv_num] = {'customer': row.get('Customer', row.get('CustomerName', '')).strip(), 'lines': []}
                    invoices[inv_num]['lines'].append({
                        'desc': row.get('Description', row.get('Item', '')),
                        'qty': row.get('Qty', row.get('Quantity', '1')),
                        'rate': row.get('Rate', row.get('Amount', '0')),
                    })
                for inv_num, data in invoices.items():
                    try:
                        customer = Customer.objects.filter(name__iexact=data['customer']).first()
                        if not customer:
                            customer = Customer.objects.create(name=data['customer'])
                        inv = Invoice.objects.create(customer=customer, invoice_number=inv_num, status='sent')
                        for idx, line in enumerate(data['lines']):
                            try:
                                qty = Decimal(line['qty'].replace('$', '').replace(',', ''))
                            except:
                                qty = Decimal('1')
                            try:
                                rate = Decimal(line['rate'].replace('$', '').replace(',', ''))
                            except:
                                rate = Decimal('0')
                            InvoiceLineItem.objects.create(
                                invoice=inv, description=line['desc'] or f'Item {idx+1}',
                                quantity=qty, rate=rate, sort_order=idx
                            )
                        imported += 1
                    except Exception as e:
                        errors += 1
                        error_log.append(f"Invoice {inv_num}: {e}")

            data_import.imported_rows = imported
            data_import.error_rows = errors
            data_import.error_log = '\n'.join(error_log[:50])
            data_import.status = 'completed' if errors == 0 else 'completed'
        except Exception as e:
            data_import.status = 'failed'
            data_import.error_log = str(e)

        data_import.completed_at = timezone.now()
        data_import.save()


# ═══════════════════════════════════════════════════════════════════
# CONTRACTS
# ═══════════════════════════════════════════════════════════════════

class ContractListView(LoginRequiredMixin, ListView):
    model = Contract
    template_name = 'premium/contract_list.html'
    context_object_name = 'contracts'

    def get_queryset(self):
        qs = Contract.objects.select_related('customer', 'division')
        if not self.request.user.is_superuser and self.request.user.division:
            qs = qs.filter(division=self.request.user.division)
        return qs


class ContractCreateView(LoginRequiredMixin, CreateView):
    model = Contract
    form_class = ContractForm
    template_name = 'premium/contract_form.html'

    def form_valid(self, form):
        if not form.instance.division_id:
            form.instance.division = self.request.user.division
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Contract '{form.instance.title}' created.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('contract-detail', kwargs={'pk': self.object.pk})


class ContractDetailView(LoginRequiredMixin, DetailView):
    model = Contract
    template_name = 'premium/contract_detail.html'
    context_object_name = 'contract'


@login_required
@require_POST
def contract_send(request, pk):
    """Mark contract as sent for signature."""
    contract = get_object_or_404(Contract, pk=pk)
    contract.status = 'sent'
    contract.sent_at = timezone.now()
    contract.save()
    messages.success(self.request, f"Contract sent to {contract.customer.name} for signature.")
    return redirect('contract-detail', pk=pk)


@login_required
@require_POST
def contract_sign(request, pk):
    """Record e-signature on contract."""
    contract = get_object_or_404(Contract, pk=pk)
    signer_name = request.POST.get('signer_name', '')
    signature_data = request.POST.get('signature_data', '')
    if signer_name and signature_data:
        contract.status = 'signed'
        contract.signed_at = timezone.now()
        contract.signer_name = signer_name
        contract.signature_data = signature_data
        contract.signer_ip = request.META.get('REMOTE_ADDR')
        contract.save()
        messages.success(self.request, f"Contract signed by {signer_name}.")
    else:
        messages.error(request, "Signature name and signature data required.")
    return redirect('contract-detail', pk=pk)


# ═══════════════════════════════════════════════════════════════════
# AI ESTIMATE TEMPLATES
# ═══════════════════════════════════════════════════════════════════

class EstimateTemplateListView(LoginRequiredMixin, ListView):
    model = EstimateTemplate
    template_name = 'premium/template_list.html'
    context_object_name = 'templates'

    def get_queryset(self):
        return EstimateTemplate.objects.filter(is_active=True).select_related('division')


class EstimateTemplateCreateView(LoginRequiredMixin, CreateView):
    model = EstimateTemplate
    form_class = EstimateTemplateForm
    template_name = 'premium/template_form.html'
    success_url = reverse_lazy('template-list')


class EstimateTemplateUpdateView(LoginRequiredMixin, UpdateView):
    model = EstimateTemplate
    form_class = EstimateTemplateForm
    template_name = 'premium/template_form.html'
    success_url = reverse_lazy('template-list')


@login_required
def ai_estimate(request, template_pk):
    """Generate an estimate from a template with AI-like calculations."""
    template = get_object_or_404(EstimateTemplate, pk=template_pk)
    customer_id = request.GET.get('customer')
    customer = get_object_or_404(Customer, pk=customer_id) if customer_id else None

    if request.method == 'POST':
        # Create estimate from template
        estimate = Estimate.objects.create(
            customer=customer or Customer.objects.first(),
            division=template.division,
            tax_rate=0.0675,
            notes=f"Generated from template: {template.name}",
            created_by=request.user,
        )
        from standard.models import EstimateLineItem
        labor_desc = f"Labor: {template.job_type or 'General'} ({template.base_labor_hours} hrs @ ${template.labor_rate}/hr)"
        EstimateLineItem.objects.create(
            estimate=estimate,
            description=labor_desc,
            quantity=template.base_labor_hours,
            rate=template.labor_rate,
            sort_order=0,
        )
        if template.material_estimate > 0:
            EstimateLineItem.objects.create(
                estimate=estimate,
                description="Materials",
                quantity=1,
                rate=template.material_estimate,
                sort_order=1,
            )
        messages.success(self.request, f"Estimate #{estimate.estimate_number} generated from {template.name}.")
        return redirect('estimate-detail', pk=estimate.pk)

    return render(request, 'premium/ai_estimate.html', {
        'template': template,
        'estimated_total': template.estimated_total,
        'customer': customer,
    })
