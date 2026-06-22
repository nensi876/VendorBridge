from decimal import Decimal
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.utils import timezone

from accounts.models import User
from vendors.models import Vendor
from procurement.models import RFQ, Quotation, Approval, PurchaseOrder, Invoice
from core.utils import log_activity


class Command(BaseCommand):
    help = 'Seed VendorBridge with sample demo data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding VendorBridge demo data...')

        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@vendorbridge.com',
                'first_name': 'System',
                'last_name': 'Admin',
                'role': User.ROLE_ADMIN,
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if not admin_user.check_password('Admin@123'):
            admin_user.set_password('Admin@123')
            admin_user.save()

        procurement, _ = User.objects.get_or_create(
            username='procurement',
            defaults={
                'email': 'procurement@vendorbridge.com',
                'first_name': 'Raj',
                'last_name': 'Sharma',
                'role': User.ROLE_PROCUREMENT,
            },
        )
        procurement.set_password('Procure@123')
        procurement.save()

        manager, _ = User.objects.get_or_create(
            username='manager',
            defaults={
                'email': 'manager@vendorbridge.com',
                'first_name': 'Priya',
                'last_name': 'Verma',
                'role': User.ROLE_MANAGER,
            },
        )
        manager.set_password('Manager@123')
        manager.save()

        vendor_users_data = [
            ('vendor1', 'TechSupply Co', 'Amit Patel'),
            ('vendor2', 'OfficeMart Ltd', 'Sneha Reddy'),
            ('vendor3', 'BuildPro Industries', 'Vikram Singh'),
        ]

        vendors = []
        for username, company, name in vendor_users_data:
            parts = name.split()
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@vendor.com',
                    'first_name': parts[0],
                    'last_name': parts[1] if len(parts) > 1 else '',
                    'role': User.ROLE_VENDOR,
                },
            )
            user.set_password('Vendor@123')
            user.save()
            vendor, _ = Vendor.objects.get_or_create(
                company_name=company,
                defaults={
                    'user': user,
                    'vendor_name': name,
                    'category': 'it' if 'Tech' in company else 'office',
                    'gst_number': f'29ABCDE{username[-1]}F1Z5',
                    'email': f'{username}@vendor.com',
                    'phone': f'98765432{username[-1]}0',
                    'address': f'123 Business Park, {company}, India',
                    'status': Vendor.STATUS_ACTIVE,
                    'rating': Decimal('4.5'),
                },
            )
            if not vendor.user:
                vendor.user = user
                vendor.save()
            vendors.append(vendor)

        for group_name in ['Admin', 'Procurement Officer', 'Manager', 'Vendor']:
            group = Group.objects.filter(name=group_name).first()
            if group:
                role_map = {
                    'Admin': admin_user,
                    'Procurement Officer': procurement,
                    'Manager': manager,
                }
                if group_name in role_map:
                    role_map[group_name].groups.add(group)
                for vu in User.objects.filter(role=User.ROLE_VENDOR):
                    if group_name == 'Vendor':
                        vu.groups.add(group)

        now = timezone.now()
        rfq_data = [
            ('Laptop Procurement 2026', 'Dell Latitude 5540', 50, 15),
            ('Office Furniture', 'Ergonomic Office Chairs', 100, 20),
            ('Network Equipment', 'Cisco Switch 48-Port', 10, 10),
        ]

        rfqs = []
        for title, product, qty, days in rfq_data:
            rfq, created = RFQ.objects.get_or_create(
                title=title,
                defaults={
                    'product_name': product,
                    'description': f'Procurement request for {product}. Quality and warranty required.',
                    'quantity': qty,
                    'deadline': now + timedelta(days=days),
                    'created_by': procurement,
                    'status': RFQ.STATUS_OPEN,
                },
            )
            if created:
                rfq.assigned_vendors.set(vendors[:2] if 'Network' not in title else vendors)
            rfqs.append(rfq)

        for rfq in rfqs:
            for i, vendor in enumerate(rfq.assigned_vendors.all()):
                price = Decimal(str(50000 + i * 5000 + rfq.quantity * 100))
                Quotation.objects.get_or_create(
                    rfq=rfq,
                    vendor=vendor,
                    defaults={
                        'quoted_price': price,
                        'delivery_timeline': 7 + i * 3,
                        'notes': f'Competitive quote from {vendor.company_name}',
                        'status': Quotation.STATUS_SUBMITTED,
                    },
                )

        rfq1 = rfqs[0]
        q1 = rfq1.quotations.first()
        if q1:
            q1.status = Quotation.STATUS_SELECTED
            q1.save()
            rfq1.status = RFQ.STATUS_AWARDED
            rfq1.save()
            approval, _ = Approval.objects.get_or_create(
                rfq=rfq1,
                quotation=q1,
                defaults={
                    'approver': manager,
                    'status': Approval.STATUS_APPROVED,
                    'remarks': 'Best price and delivery timeline.',
                    'approval_date': now,
                },
            )
            po, _ = PurchaseOrder.objects.get_or_create(
                quotation=q1,
                defaults={
                    'vendor': q1.vendor,
                    'amount': q1.quoted_price,
                    'created_by': procurement,
                    'status': PurchaseOrder.STATUS_ISSUED,
                },
            )
            gst = (po.amount * Decimal('18') / Decimal('100')).quantize(Decimal('0.01'))
            Invoice.objects.get_or_create(
                purchase_order=po,
                defaults={
                    'subtotal': po.amount,
                    'gst': gst,
                    'tax': Decimal('0.00'),
                    'grand_total': po.amount + gst,
                    'status': Invoice.STATUS_SENT,
                    'created_by': procurement,
                },
            )

        rfq2 = rfqs[1]
        q2 = rfq2.quotations.first()
        if q2:
            Approval.objects.get_or_create(
                rfq=rfq2,
                quotation=q2,
                defaults={'status': Approval.STATUS_PENDING},
            )

        log_activity(admin_user, 'Demo data seeded', 'System')

        self.stdout.write(self.style.SUCCESS('Demo data seeded successfully!'))
        self.stdout.write('')
        self.stdout.write('Login credentials:')
        self.stdout.write('  Admin:       admin / Admin@123')
        self.stdout.write('  Procurement: procurement / Procure@123')
        self.stdout.write('  Manager:     manager / Manager@123')
        self.stdout.write('  Vendor:      vendor1 / Vendor@123')
