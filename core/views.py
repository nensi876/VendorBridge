import csv
import json

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import role_required
from accounts.models import User
from core.models import ActivityLog
from core.utils import log_activity
from procurement.models import Approval, Invoice, PurchaseOrder, Quotation, RFQ
from vendors.models import Vendor


@login_required
def dashboard(request):
    if request.user.is_vendor_role:
        return redirect('procurement:vendor_rfq_list')

    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    stats = {
        'total_vendors': Vendor.objects.filter(status=Vendor.STATUS_ACTIVE).count(),
        'active_rfqs': RFQ.objects.filter(status=RFQ.STATUS_OPEN).count(),
        'pending_approvals': Approval.objects.filter(status=Approval.STATUS_PENDING).count(),
        'purchase_orders': PurchaseOrder.objects.count(),
        'invoices': Invoice.objects.count(),
        'monthly_spending': PurchaseOrder.objects.filter(
            created_at__gte=month_start
        ).aggregate(total=Sum('amount'))['total'] or 0,
    }

    recent_activities = ActivityLog.objects.select_related('user')[:10]
    recent_rfqs = RFQ.objects.order_by('-created_at')[:5]
    pending_approvals = Approval.objects.filter(
        status=Approval.STATUS_PENDING
    ).select_related('rfq')[:5]

    monthly_trends = (
        PurchaseOrder.objects
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('month')[:6]
    )
    trend_labels = [item['month'].strftime('%b %Y') if item['month'] else '' for item in monthly_trends]
    trend_values = [float(item['total'] or 0) for item in monthly_trends]

    approval_stats = list(Approval.objects.values('status').annotate(count=Count('id')))

    return render(request, 'core/dashboard.html', {
        'stats': stats,
        'recent_activities': recent_activities,
        'recent_rfqs': recent_rfqs,
        'pending_approvals': pending_approvals,
        'trend_labels_json': json.dumps(trend_labels),
        'trend_values_json': json.dumps(trend_values),
        'approval_stats': approval_stats,
    })


@login_required
def activity_log_list(request):
    logs = ActivityLog.objects.select_related('user').all()
    module = request.GET.get('module', '')
    if module:
        logs = logs.filter(module__icontains=module)
    if not request.user.is_admin_role:
        logs = logs.filter(user=request.user)
    return render(request, 'core/activity_log.html', {'logs': logs, 'selected_module': module})


@login_required
def mark_notification_read(request, pk):
    notification = get_object_or_404(request.user.notifications, pk=pk)
    notification.is_read = True
    notification.save()
    if notification.link:
        return redirect(notification.link)
    return redirect('core:dashboard')


@login_required
def mark_all_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    messages_success = 'All notifications marked as read.'
    from django.contrib import messages
    messages.success(request, messages_success)
    return redirect('core:dashboard')


@login_required
@role_required(User.ROLE_ADMIN, User.ROLE_MANAGER, User.ROLE_PROCUREMENT)
def reports(request):
    vendor_performance = (
        Vendor.objects
        .annotate(
            po_count=Count('purchase_orders'),
            total_value=Sum('purchase_orders__amount'),
            quotation_count=Count('quotations'),
        )
        .order_by('-total_value')[:10]
    )

    procurement_summary = {
        'total_rfqs': RFQ.objects.count(),
        'total_quotations': Quotation.objects.count(),
        'total_pos': PurchaseOrder.objects.count(),
        'total_invoices': Invoice.objects.count(),
        'total_spending': PurchaseOrder.objects.aggregate(t=Sum('amount'))['t'] or 0,
    }

    monthly_trends = (
        PurchaseOrder.objects
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-month')[:12]
    )

    approval_statistics = Approval.objects.values('status').annotate(count=Count('id'))

    spending_by_category = (
        Vendor.objects
        .values('category')
        .annotate(total=Sum('purchase_orders__amount'))
        .order_by('-total')
    )

    return render(request, 'core/reports.html', {
        'vendor_performance': vendor_performance,
        'procurement_summary': procurement_summary,
        'monthly_trends': monthly_trends,
        'approval_statistics': approval_statistics,
        'spending_by_category': spending_by_category,
    })


@login_required
@role_required(User.ROLE_ADMIN, User.ROLE_MANAGER, User.ROLE_PROCUREMENT)
def export_reports_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="vendorbridge_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Report Type', 'Detail', 'Value'])

    writer.writerow(['Summary', 'Total RFQs', RFQ.objects.count()])
    writer.writerow(['Summary', 'Total POs', PurchaseOrder.objects.count()])
    writer.writerow(['Summary', 'Total Invoices', Invoice.objects.count()])
    total_spending = PurchaseOrder.objects.aggregate(t=Sum('amount'))['t'] or 0
    writer.writerow(['Summary', 'Total Spending', total_spending])

    writer.writerow([])
    writer.writerow(['Vendor Performance', 'Company', 'PO Count', 'Total Value'])
    for v in Vendor.objects.annotate(
        po_count=Count('purchase_orders'),
        total_value=Sum('purchase_orders__amount'),
    ):
        writer.writerow(['Vendor', v.company_name, v.po_count, v.total_value or 0])

    writer.writerow([])
    writer.writerow(['Approval Statistics', 'Status', 'Count'])
    for item in Approval.objects.values('status').annotate(count=Count('id')):
        writer.writerow(['Approval', item['status'], item['count']])

    log_activity(request.user, 'Exported reports to CSV', 'Reports')
    return response
