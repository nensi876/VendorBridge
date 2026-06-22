from django.contrib import admin
from .models import RFQ, Quotation, Approval, PurchaseOrder, Invoice


@admin.register(RFQ)
class RFQAdmin(admin.ModelAdmin):
    list_display = ['rfq_number', 'title', 'status', 'deadline', 'created_by', 'created_at']
    list_filter = ['status']
    search_fields = ['rfq_number', 'title', 'product_name']
    filter_horizontal = ['assigned_vendors']


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ['rfq', 'vendor', 'quoted_price', 'delivery_timeline', 'status', 'submission_date']
    list_filter = ['status']


@admin.register(Approval)
class ApprovalAdmin(admin.ModelAdmin):
    list_display = ['rfq', 'approver', 'status', 'approval_date']
    list_filter = ['status']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['po_number', 'vendor', 'amount', 'status', 'created_at']
    list_filter = ['status']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'purchase_order', 'grand_total', 'status', 'created_at']
    list_filter = ['status']
