from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from accounts.models import User
from core.utils import log_activity
from vendors.forms import VendorForm, VendorSearchForm
from vendors.models import Vendor


@login_required
@role_required(User.ROLE_ADMIN, User.ROLE_PROCUREMENT)
def vendor_list(request):
    vendors = Vendor.objects.all()
    form = VendorSearchForm(request.GET or None)
    if form.is_valid():
        q = form.cleaned_data.get('q')
        category = form.cleaned_data.get('category')
        status = form.cleaned_data.get('status')
        if q:
            vendors = vendors.filter(
                Q(vendor_name__icontains=q) |
                Q(company_name__icontains=q) |
                Q(email__icontains=q) |
                Q(gst_number__icontains=q)
            )
        if category:
            vendors = vendors.filter(category=category)
        if status:
            vendors = vendors.filter(status=status)
    return render(request, 'vendors/list.html', {'vendors': vendors, 'search_form': form})


@login_required
@role_required(User.ROLE_ADMIN, User.ROLE_PROCUREMENT)
def vendor_detail(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    return render(request, 'vendors/detail.html', {'vendor': vendor})


@login_required
@role_required(User.ROLE_ADMIN, User.ROLE_PROCUREMENT)
def vendor_create(request):
    form = VendorForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        vendor = form.save()
        log_activity(request.user, f'Created vendor {vendor.company_name}', 'Vendor Management')
        messages.success(request, 'Vendor created successfully.')
        return redirect('vendors:detail', pk=vendor.pk)
    return render(request, 'vendors/form.html', {'form': form, 'title': 'Add Vendor'})


@login_required
@role_required(User.ROLE_ADMIN, User.ROLE_PROCUREMENT)
def vendor_edit(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    form = VendorForm(request.POST or None, instance=vendor)
    if request.method == 'POST' and form.is_valid():
        form.save()
        log_activity(request.user, f'Updated vendor {vendor.company_name}', 'Vendor Management')
        messages.success(request, 'Vendor updated successfully.')
        return redirect('vendors:detail', pk=vendor.pk)
    return render(request, 'vendors/form.html', {'form': form, 'title': 'Edit Vendor', 'vendor': vendor})


@login_required
@role_required(User.ROLE_ADMIN)
def vendor_delete(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    if request.method == 'POST':
        name = vendor.company_name
        vendor.delete()
        log_activity(request.user, f'Deleted vendor {name}', 'Vendor Management')
        messages.success(request, 'Vendor deleted successfully.')
        return redirect('vendors:list')
    return render(request, 'vendors/confirm_delete.html', {'vendor': vendor})
