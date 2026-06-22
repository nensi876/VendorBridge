from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from vendors.models import Vendor


def generate_rfq_number():
    year = timezone.now().year
    count = RFQ.objects.filter(created_at__year=year).count() + 1
    return f'RFQ-{year}-{count:05d}'


def generate_po_number():
    year = timezone.now().year
    count = PurchaseOrder.objects.filter(created_at__year=year).count() + 1
    return f'PO-{year}-{count:05d}'


def generate_invoice_number():
    year = timezone.now().year
    count = Invoice.objects.filter(created_at__year=year).count() + 1
    return f'INV-{year}-{count:05d}'


class RFQ(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_OPEN = 'open'
    STATUS_CLOSED = 'closed'
    STATUS_AWARDED = 'awarded'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_OPEN, 'Open'),
        (STATUS_CLOSED, 'Closed'),
        (STATUS_AWARDED, 'Awarded'),
    ]

    rfq_number = models.CharField(max_length=30, unique=True, default=generate_rfq_number)
    title = models.CharField(max_length=200)
    product_name = models.CharField(max_length=200)
    description = models.TextField()
    quantity = models.PositiveIntegerField(default=1)
    deadline = models.DateTimeField()
    attachment = models.FileField(upload_to='rfq_attachments/', blank=True, null=True)
    assigned_vendors = models.ManyToManyField(Vendor, blank=True, related_name='assigned_rfqs')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_rfqs',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'RFQ'
        verbose_name_plural = 'RFQs'

    def __str__(self):
        return f'{self.rfq_number} - {self.title}'

    @property
    def is_deadline_passed(self):
        return timezone.now() > self.deadline

    @property
    def quotation_count(self):
        return self.quotations.count()


class Quotation(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_SUBMITTED = 'submitted'
    STATUS_SELECTED = 'selected'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SUBMITTED, 'Submitted'),
        (STATUS_SELECTED, 'Selected'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE, related_name='quotations')
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='quotations')
    quoted_price = models.DecimalField(max_digits=12, decimal_places=2)
    delivery_timeline = models.PositiveIntegerField(help_text='Delivery timeline in days')
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SUBMITTED)
    submission_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['quoted_price']
        unique_together = ['rfq', 'vendor']

    def __str__(self):
        return f'{self.vendor.company_name} - {self.rfq.rfq_number}'


class Approval(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    rfq = models.ForeignKey(RFQ, on_delete=models.CASCADE, related_name='approvals')
    quotation = models.ForeignKey(
        Quotation,
        on_delete=models.CASCADE,
        related_name='approvals',
        null=True,
        blank=True,
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='approvals',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    remarks = models.TextField(blank=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Approval for {self.rfq.rfq_number} - {self.status}'


class PurchaseOrder(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_ISSUED = 'issued'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_ISSUED, 'Issued'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    po_number = models.CharField(max_length=30, unique=True, default=generate_po_number)
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name='purchase_orders')
    quotation = models.OneToOneField(Quotation, on_delete=models.PROTECT, related_name='purchase_order')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ISSUED)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_pos',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.po_number


class Invoice(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_SENT = 'sent'
    STATUS_PAID = 'paid'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SENT, 'Sent'),
        (STATUS_PAID, 'Paid'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=30, unique=True, default=generate_invoice_number)
    purchase_order = models.OneToOneField(PurchaseOrder, on_delete=models.PROTECT, related_name='invoice')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    gst = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    grand_total = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_invoices',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.invoice_number
