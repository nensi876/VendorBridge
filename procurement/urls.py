from django.urls import path
from . import views

app_name = 'procurement'

urlpatterns = [
    # RFQ
    path('rfq/', views.rfq_list, name='rfq_list'),
    path('rfq/create/', views.rfq_create, name='rfq_create'),
    path('rfq/<int:pk>/', views.rfq_detail, name='rfq_detail'),
    path('rfq/<int:pk>/edit/', views.rfq_edit, name='rfq_edit'),
    path('rfq/<int:pk>/delete/', views.rfq_delete, name='rfq_delete'),
    path('rfq/<int:pk>/assign/', views.rfq_assign_vendors, name='rfq_assign'),
    # Vendor RFQ
    path('vendor/rfq/', views.vendor_rfq_list, name='vendor_rfq_list'),
    path('vendor/rfq/<int:pk>/', views.vendor_rfq_detail, name='vendor_rfq_detail'),
    # Quotations
    path('quotations/', views.quotation_list, name='quotation_list'),
    path('quotations/<int:rfq_pk>/compare/', views.quotation_compare, name='quotation_compare'),
    path('quotations/submit/<int:rfq_pk>/', views.quotation_submit, name='quotation_submit'),
    path('quotations/<int:pk>/edit/', views.quotation_edit, name='quotation_edit'),
    path('quotations/<int:rfq_pk>/approve/<int:quotation_pk>/', views.request_approval, name='request_approval'),
    # Approvals
    path('approvals/', views.approval_list, name='approval_list'),
    path('approvals/<int:pk>/', views.approval_detail, name='approval_detail'),
    path('approvals/<int:pk>/<str:action>/', views.approval_action, name='approval_action'),
    # Purchase Orders
    path('po/', views.po_list, name='po_list'),
    path('po/generate/<int:quotation_pk>/', views.po_generate, name='po_generate'),
    path('po/<int:pk>/', views.po_detail, name='po_detail'),
    path('po/<int:pk>/pdf/', views.po_pdf, name='po_pdf'),
    path('vendor/po/', views.vendor_po_list, name='vendor_po_list'),
    # Invoices
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/generate/<int:po_pk>/', views.invoice_generate, name='invoice_generate'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/print/', views.invoice_print, name='invoice_print'),
    path('invoices/<int:pk>/pdf/', views.invoice_pdf, name='invoice_pdf'),
    path('invoices/<int:pk>/send/', views.invoice_send_email, name='invoice_send_email'),
]
