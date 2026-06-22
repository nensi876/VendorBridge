from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import role_required
from accounts.models import User
from core.models import Notification
from core.utils import create_notification, log_activity, notify_role
from procurement.forms import ApprovalActionForm, AssignVendorsForm, QuotationForm, RFQForm
from procurement.models import Approval, Invoice, PurchaseOrder, Quotation, RFQ
from procurement.pdf_utils import generate_invoice_pdf, generate_po_pdf, send_invoice_email
from vendors.models import Vendor


def _get_vendor_for_user(user):
    return getattr(user, 'vendor_profile', None)


# ── RFQ Views ──────────────────────────────────────────────────────────────

@login_required
@role_required(User.ROLE_ADMIN, User.ROLE_PROCUREMENT)
def rfq_list(request):
    rfqs = RFQ.objects.all()
    status = request.GET.get('status', '')
    q = request.GET.get('q', '')
    if status:
        rfqs = rfqs.filter(status=status)
    if q:
        rfqs = rfqs.filter(
            Q(rfq_number__icontains=q) | Q(title__icontains=q) | Q(product_name__icontains=q)
        )
    return render(request, 'procurement/rfq_list.html', {'rfqs': rfqs, 'q': q, 'selected_status': status})


@login_required
@role_required(User.ROLE_ADMIN, User.ROLE_PROCUREMENT)
def rfq_detail(request, pk):
    rfq = get_object_or_404(RFQ, pk=pk)
    quotations = rfq.quotations.select_related('vendor').all()
    approvals = rfq.approvals.select_related('approver', 'quotation').all()
    return render(request, 'procurement/rfq_detail.html', {
        'rfq': rfq,
        'quotations': quotations,
        'approvals': approvals,
    })


@login_required
@role_required(User.ROLE_ADMIN, User.ROLE_PROCUREMENT)
def rfq_create(request):
    form = RFQForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        rfq = form.save(commit=False)
        rfq.created_by = request.user
        rfq.save()
        log_activity(request.user, f'Created RFQ {rfq.rfq_number}', 'RFQ')
        notify_role(User.ROLE_MANAGER, f'New RFQ: {rfq.title}',
                    f'RFQ {rfq.rfq_number} requires review.', Notification.TYPE_RFQ,
                    f'/procurement/rfq/{rfq.pk}/')
        messages.success(request, 'RFQ created successfully.')
        return redirect('procurement:rfq_detail', pk=rfq.pk)
    return render(request, 'procurement/rfq_form.html', {'form': form, 'title': 'Create RFQ'})


@login_required
@role_required(User.ROLE_ADMIN, User.ROLE_PROCUREMENT)
def rfq_edit(request, pk):
    rfq = get_object_or_404(RFQ, pk=pk)
    form = RFQForm(request.POST or None, request.FILES or None, instance=rfq)
    if request.method == 'POST' and form.is_valid():
        form.save()
        log_activity(request.user, f'Updated RFQ {rfq.rfq_number}', 'RFQ')
        messages.success(request, 'RFQ updated successfully.')
        return redirect('procurement:rfq_detail', pk=rfq.pk)
    return render(request, 'procurement/rfq_form.html', {'form': form, 'title': 'Edit RFQ', 'rfq': rfq})


@login_required
@role_required(User.ROLE_ADMIN, User.ROLE_PROCUREMENT)
def rfq_delete(request, pk):
    rfq = get_object_or_404(RFQ, pk=pk)
    if request.method == 'POST':
        number = rfq.rfq_number
        rfq.delete()
        log_activity(request.user, f'Deleted RFQ {number}', 'RFQ')
        messages.success(request, 'RFQ deleted successfully.')
        return redirect('procurement:rfq_list')
    return render(request, 'procurement/rfq_confirm_delete.html', {'rfq': rfq})


@login_required
@role_required(User.ROLE_ADMIN, User.ROLE_PROCUREMENT)
def rfq_assign_vendors(request, pk):
    rfq = get_object_or_404(RFQ, pk=pk)
    form = AssignVendorsForm(request.POST or None, instance=rfq)
    if request.method == 'POST' and form.is_valid():
        form.save()
        for vendor in rfq.assigned_vendors.all():
            if vendor.user:
                create_notification(
                    vendor.user,
                    f'RFQ Assigned: {rfq.rfq_number}',
                    f'You have been assigned to RFQ "{rfq.title}".',
                    Notification.TYPE_RFQ,
                    f'/procurement/vendor/rfq/{rfq.pk}/',
                )
        log_activity(request.user, f'Assigned vendors to RFQ {rfq.rfq_number}', 'RFQ')
        messages.success(request, 'Vendors assigned successfully.')
        return redirect('procurement:rfq_detail', pk=rfq.pk)
    return render(request, 'procurement/rfq_assign.html', {'form': form, 'rfq': rfq})


# ── Vendor RFQ Views ───────────────────────────────────────────────────────

@login_required
@role_required(User.ROLE_VENDOR)
def vendor_rfq_list(request):
    vendor = _get_vendor_for_user(request.user)
    if not vendor:
        messages.warning(request, 'No vendor profile linked to your account.')
        return render(request, 'procurement/vendor_rfq_list.html', {'rfqs': []})
    rfqs = vendor.assigned_rfqs.filter(status=RFQ.STATUS_OPEN)
    return render(request, 'procurement/vendor_rfq_list.html', {'rfqs': rfqs, 'vendor': vendor})


@login_required
@role_required(User.ROLE_VENDOR)
def vendor_rfq_detail(request, pk):
    vendor = _get_vendor_for_user(request.user)
    rfq = get_object_or_404(RFQ, pk=pk, assigned_vendors=vendor)
    quotation = rfq.quotations.filter(vendor=vendor).first()
    return render(request, 'procurement/vendor_rfq_detail.html', {
        'rfq': rfq,
        'vendor': vendor,
        'quotation': quotation,
    })


# ── Quotation Views ────────────────────────────────────────────────────────

@login_required
@role_required(User.ROLE_VENDOR)
def quotation_submit(request, rfq_pk):
    vendor = _get_vendor_for_user(request.user)
    rfq = get_object_or_404(RFQ, pk=rfq_pk, assigned_vendors=vendor)
    if rfq.is_deadline_passed:
        messages.error(request, 'The deadline for this RFQ has passed.')
        return redirect('procurement:vendor_rfq_detail', pk=rfq.pk)
    quotation, created = Quotation.objects.get_or_create(rfq=rfq, vendor=vendor)
    form = QuotationForm(request.POST or None, instance=quotation)
    if request.method == 'POST' and form.is_valid():
        q = form.save(commit=False)
        q.status = Quotation.STATUS_SUBMITTED
        q.save()
        log_activity(request.user, f'Submitted quotation for {rfq.rfq_number}', 'Quotation')
        notify_role(User.ROLE_PROCUREMENT, f'New Quotation: {rfq.rfq_number}',
                    f'{vendor.company_name} submitted a quotation.', Notification.TYPE_RFQ)
        messages.success(request, 'Quotation submitted successfully.')
        return redirect('procurement:vendor_rfq_detail', pk=rfq.pk)
    return render(request, 'procurement/quotation_form.html', {
        'form': form, 'rfq': rfq, 'title': 'Submit Quotation',
    })


@login_required
@role_required(User.ROLE_VENDOR)
def quotation_edit(request, pk):
    vendor = _get_vendor_for_user(request.user)
    quotation = get_object_or_404(Quotation, pk=pk, vendor=vendor)
    if quotation.rfq.is_deadline_passed:
        messages.error(request, 'The deadline for this RFQ has passed. Editing is not allowed.')
        return redirect('procurement:vendor_rfq_detail', pk=quotation.rfq.pk)
    form = QuotationForm(request.POST or None, instance=quotation)
    if request.method == 'POST' and form.is_valid():
        form.save()
        log_activity(request.user, f'Updated quotation for {quotation.rfq.rfq_number}', 'Quotation')
        messages.success(request, 'Quotation updated successfully.')
        return redirect('procurement:vendor_rfq_detail', pk=quotation.rfq.pk)
    return render(request, 'procurement/quotation_form.html', {
        'form': form, 'rfq': quotation.rfq, 'title': 'Edit Quotation',
    })


@login_required
def quotation_list(request):
    if request.user.is_vendor_role:
        vendor = _get_vendor_for_user(request.user)
        quotations = Quotation.objects.filter(vendor=vendor) if vendor else Quotation.objects.none()
    else:
        quotations = Quotation.objects.select_related('rfq', 'vendor').all()
    return render(request, 'procurement/quotation_list.html', {'quotations': quotations})


@login_required
@role_required(User.ROLE_ADMIN, User.ROLE_PROCUREMENT)
def quotation_compare(request, rfq_pk):
    rfq = get_object_or_404(RFQ, pk=rfq_pk)
    quotations = list(rfq.quotations.filter(status=Quotation.STATUS_SUBMITTED).select_related('vendor'))
    sort_by = request.GET.get('sort', 'price')
    filter_vendor = request.GET.get('vendor', '')

    if filter_vendor:
        quotations = [q for q in quotations if filter_vendor.lower() in q.vendor.company_name.lower()]

    if sort_by == 'delivery':
        quotations.sort(key=lambda q: q.delivery_timeline)
    elif sort_by == 'rating':
        quotations.sort(key=lambda q: q.vendor.rating, reverse=True)
    else:
        quotations.sort(key=lambda q: q.quoted_price)

    lowest_price = min((q.quoted_price for q in quotations), default=None)
    fastest_delivery = min((q.delivery_timeline for q in quotations), default=None)

    return render(request, 'procurement/quotation_compare.html', {
        'rfq': rfq,
        'quotations': quotations,
        'lowest_price': lowest_price,
        'fastest_delivery': fastest_delivery,
        'sort_by': sort_by,
        'filter_vendor': filter_vendor,
    })


# ── Approval Views ─────────────────────────────────────────────────────────

@login_required
@role_required(User.ROLE_ADMIN, User.ROLE_MANAGER)
def approval_list(request):
    approvals = Approval.objects.select_related('rfq', 'approver', 'quotation').all()
    status = request.GET.get('status', '')
    if status:
        approvals = approvals.filter(status=status)
    return render(request, 'procurement/approval_list.html', {
        'approvals': approvals,
        'selected_status': status,
    })


@login_required
@role_required(User.ROLE_ADMIN, User.ROLE_MANAGER)
def approval_detail(request, pk):
    approval = get_object_or_404(Approval, pk=pk)
    timeline = approval.rfq.approvals.select_related('approver').order_by('created_at')
    return render(request, 'procurement/approval_detail.html', {
        'approval': approval,
        'timeline': timeline,
    })


@login_required
@role_required(User.ROLE_ADMIN, User.ROLE_PROCUREMENT)
def request_approval(request, rfq_pk, quotation_pk):
    rfq = get_object_or_404(RFQ, pk=rfq_pk)
    quotation = get_object_or_404(Quotation, pk=quotation_pk, rfq=rfq)
    approval = Approval.objects.create(rfq=rfq, quotation=quotation)
    notify_role(User.ROLE_MANAGER, f'Approval Required: {rfq.rfq_number}',
                f'Quotation from {quotation.vendor.company_name} needs approval.',
                Notification.TYPE_APPROVAL, f'/procurement/approvals/{approval.pk}/')
    log_activity(request.user, f'Requested approval for {rfq.rfq_number}', 'Approval')
    messages.success(request, 'Approval request submitted.')
    return redirect('procurement:quotation_compare', rfq_pk=rfq.pk)


@login_required
@role_required(User.ROLE_ADMIN, User.ROLE_MANAGER)
def approval_action(request, pk, action):
    approval = get_object_or_404(Approval, pk=pk, status=Approval.STATUS_PENDING)
    form = ApprovalActionForm(request.POST or None)
    if request.method == 'POST':
        remarks = request.POST.get('remarks', '')
        approval.approver = request.user
        approval.remarks = remarks
        approval.approval_date = timezone.now()
        if action == 'approve':
            approval.status = Approval.STATUS_APPROVED
            approval.quotation.status = Quotation.STATUS_SELECTED
            approval.quotation.save()
            approval.rfq.status = RFQ.STATUS_AWARDED
            approval.rfq.save()
            messages.success(request, 'Request approved successfully.')
        else:
            approval.status = Approval.STATUS_REJECTED
            messages.warning(request, 'Request rejected.')
        approval.save()
        log_activity(request.user, f'{action.title()}d approval for {approval.rfq.rfq_number}', 'Approval')
        notify_role(User.ROLE_PROCUREMENT, f'Approval {action.title()}d: {approval.rfq.rfq_number}',
                    f'Approval for {approval.rfq.rfq_number} was {action}d.', Notification.TYPE_APPROVAL)
        return redirect('procurement:approval_list')
    return render(request, 'procurement/approval_action.html', {'approval': approval, 'action': action, 'form': form})


# ── Purchase Order Views ───────────────────────────────────────────────────

@login_required
@role_required(User.ROLE_ADMIN, User.ROLE_PROCUREMENT)
def po_list(request):
    pos = PurchaseOrder.objects.select_related('vendor', 'quotation').all()
    return render(request, 'procurement/po_list.html', {'purchase_orders': pos})


@login_required
@role_required(User.ROLE_ADMIN, User.ROLE_PROCUREMENT)
def po_generate(request, quotation_pk):
    quotation = get_object_or_404(Quotation, pk=quotation_pk, status=Quotation.STATUS_SELECTED)
    if hasattr(quotation, 'purchase_order'):
        messages.info(request, 'Purchase Order already exists for this quotation.')
        return redirect('procurement:po_detail', pk=quotation.purchase_order.pk)
    po = PurchaseOrder.objects.create(
        vendor=quotation.vendor,
        quotation=quotation,
        amount=quotation.quoted_price,
        created_by=request.user,
    )
    if quotation.vendor.user:
        create_notification(
            quotation.vendor.user,
            f'New PO: {po.po_number}',
            f'Purchase Order {po.po_number} has been issued.',
            Notification.TYPE_GENERAL,
            f'/procurement/po/{po.pk}/',
        )
    log_activity(request.user, f'Generated PO {po.po_number}', 'Purchase Order')
    messages.success(request, f'Purchase Order {po.po_number} generated.')
    return redirect('procurement:po_detail', pk=po.pk)


@login_required
def po_detail(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)
    if request.user.is_vendor_role:
        vendor = _get_vendor_for_user(request.user)
        if not vendor or po.vendor != vendor:
            messages.error(request, 'Access denied.')
            return redirect('procurement:vendor_po_list')
    return render(request, 'procurement/po_detail.html', {'po': po})


@login_required
@role_required(User.ROLE_VENDOR)
def vendor_po_list(request):
    vendor = _get_vendor_for_user(request.user)
    pos = PurchaseOrder.objects.filter(vendor=vendor) if vendor else PurchaseOrder.objects.none()
    return render(request, 'procurement/vendor_po_list.html', {'purchase_orders': pos})


@login_required
def po_pdf(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)
    pdf = generate_po_pdf(po)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{po.po_number}.pdf"'
    return response


# ── Invoice Views ──────────────────────────────────────────────────────────

@login_required
@role_required(User.ROLE_ADMIN, User.ROLE_PROCUREMENT)
def invoice_list(request):
    invoices = Invoice.objects.select_related('purchase_order__vendor').all()
    return render(request, 'procurement/invoice_list.html', {'invoices': invoices})


@login_required
@role_required(User.ROLE_ADMIN, User.ROLE_PROCUREMENT)
def invoice_generate(request, po_pk):
    po = get_object_or_404(PurchaseOrder, pk=po_pk)
    if hasattr(po, 'invoice'):
        messages.info(request, 'Invoice already exists for this PO.')
        return redirect('procurement:invoice_detail', pk=po.invoice.pk)
    subtotal = po.amount
    gst_rate = Decimal(str(settings.VENDORBRIDGE_GST_RATE))
    gst = (subtotal * gst_rate / Decimal('100')).quantize(Decimal('0.01'))
    tax = Decimal('0.00')
    grand_total = subtotal + gst + tax
    invoice = Invoice.objects.create(
        purchase_order=po,
        subtotal=subtotal,
        gst=gst,
        tax=tax,
        grand_total=grand_total,
        created_by=request.user,
    )
    log_activity(request.user, f'Generated invoice {invoice.invoice_number}', 'Invoice')
    notify_role(User.ROLE_ADMIN, f'New Invoice: {invoice.invoice_number}',
                f'Invoice generated for PO {po.po_number}.', Notification.TYPE_INVOICE)
    messages.success(request, f'Invoice {invoice.invoice_number} generated.')
    return redirect('procurement:invoice_detail', pk=invoice.pk)


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, 'procurement/invoice_detail.html', {'invoice': invoice})


@login_required
def invoice_print(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, 'procurement/invoice_print.html', {'invoice': invoice})


@login_required
def invoice_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    pdf = generate_invoice_pdf(invoice)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{invoice.invoice_number}.pdf"'
    return response


@login_required
@role_required(User.ROLE_ADMIN, User.ROLE_PROCUREMENT)
def invoice_send_email(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    recipient = invoice.purchase_order.vendor.email
    send_invoice_email(invoice, recipient)
    invoice.status = Invoice.STATUS_SENT
    invoice.save()
    log_activity(request.user, f'Sent invoice {invoice.invoice_number} via email', 'Invoice')
    messages.success(request, f'Invoice sent to {recipient}.')
    return redirect('procurement:invoice_detail', pk=invoice.pk)
