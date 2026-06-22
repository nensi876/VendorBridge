from django.contrib import admin
from .models import Vendor


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'vendor_name', 'category', 'status', 'rating', 'created_at']
    list_filter = ['status', 'category']
    search_fields = ['company_name', 'vendor_name', 'email', 'gst_number']
