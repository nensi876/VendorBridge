from django import forms

from .models import Vendor


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = [
            'vendor_name', 'company_name', 'category', 'gst_number',
            'email', 'phone', 'address', 'status', 'rating',
        ]
        widgets = {
            'vendor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'gst_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'max': '5'}),
        }


class VendorSearchForm(forms.Form):
    q = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Search vendors...',
    }))
    category = forms.ChoiceField(
        required=False,
        choices=[('', 'All Categories')] + list(Vendor.CATEGORY_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + list(Vendor.STATUS_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
