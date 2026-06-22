from django import forms

from procurement.models import Approval, Quotation, RFQ
from vendors.models import Vendor


class RFQForm(forms.ModelForm):
    class Meta:
        model = RFQ
        fields = ['title', 'product_name', 'description', 'quantity', 'deadline', 'attachment', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }


class AssignVendorsForm(forms.ModelForm):
    assigned_vendors = forms.ModelMultipleChoiceField(
        queryset=Vendor.objects.filter(status=Vendor.STATUS_ACTIVE),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
    )

    class Meta:
        model = RFQ
        fields = ['assigned_vendors']


class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ['quoted_price', 'delivery_timeline', 'notes']
        widgets = {
            'quoted_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'delivery_timeline': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ApprovalForm(forms.ModelForm):
    class Meta:
        model = Approval
        fields = ['status', 'remarks']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ApprovalActionForm(forms.Form):
    remarks = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Add remarks...'}),
    )
