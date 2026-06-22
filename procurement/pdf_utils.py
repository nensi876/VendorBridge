from io import BytesIO

from django.conf import settings
from django.core.mail import EmailMessage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _build_pdf(title, lines):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle('Header', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1e3a5f'))
    story = [Paragraph(title, header_style), Spacer(1, 0.3 * inch)]
    for label, value in lines:
        story.append(Paragraph(f'<b>{label}:</b> {value}', styles['Normal']))
        story.append(Spacer(1, 0.1 * inch))
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_po_pdf(purchase_order):
    po = purchase_order
    lines = [
        ('PO Number', po.po_number),
        ('Vendor', po.vendor.company_name),
        ('RFQ', po.quotation.rfq.rfq_number),
        ('Product', po.quotation.rfq.product_name),
        ('Quantity', str(po.quotation.rfq.quantity)),
        ('Amount', f'₹{po.amount:,.2f}'),
        ('Status', po.get_status_display()),
        ('Created', po.created_at.strftime('%d %b %Y')),
    ]
    return _build_pdf('Purchase Order', lines)


def generate_invoice_pdf(invoice):
    inv = invoice
    po = inv.purchase_order
    lines = [
        ('Invoice Number', inv.invoice_number),
        ('PO Number', po.po_number),
        ('Vendor', po.vendor.company_name),
        ('Subtotal', f'₹{inv.subtotal:,.2f}'),
        ('GST', f'₹{inv.gst:,.2f}'),
        ('Tax', f'₹{inv.tax:,.2f}'),
        ('Grand Total', f'₹{inv.grand_total:,.2f}'),
        ('Status', inv.get_status_display()),
        ('Date', inv.created_at.strftime('%d %b %Y')),
    ]
    return _build_pdf('Tax Invoice', lines)


def send_invoice_email(invoice, recipient_email):
    pdf_buffer = generate_invoice_pdf(invoice)
    email = EmailMessage(
        subject=f'Invoice {invoice.invoice_number} from VendorBridge',
        body=(
            f'Dear {invoice.purchase_order.vendor.vendor_name},\n\n'
            f'Please find attached invoice {invoice.invoice_number} '
            f'for PO {invoice.purchase_order.po_number}.\n\n'
            f'Grand Total: ₹{invoice.grand_total:,.2f}\n\n'
            f'Regards,\nVendorBridge Procurement Team'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient_email],
    )
    email.attach(f'{invoice.invoice_number}.pdf', pdf_buffer.getvalue(), 'application/pdf')
    email.send()
    return True
