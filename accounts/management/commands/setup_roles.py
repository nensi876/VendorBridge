from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from accounts.models import User
from procurement.models import RFQ, Quotation, Approval, PurchaseOrder, Invoice
from vendors.models import Vendor
from core.models import Notification, ActivityLog


class Command(BaseCommand):
    help = 'Set up Django groups and permissions for VendorBridge roles'

    def handle(self, *args, **options):
        models = [User, Vendor, RFQ, Quotation, Approval, PurchaseOrder, Invoice, Notification, ActivityLog]
        all_perms = []
        for model in models:
            ct = ContentType.objects.get_for_model(model)
            perms = Permission.objects.filter(content_type=ct)
            all_perms.extend(perms)

        groups_config = {
            'Admin': all_perms,
            'Procurement Officer': Permission.objects.filter(
                codename__in=[
                    'add_rfq', 'change_rfq', 'view_rfq', 'delete_rfq',
                    'add_quotation', 'change_quotation', 'view_quotation',
                    'add_purchaseorder', 'view_purchaseorder',
                    'add_invoice', 'view_invoice',
                    'add_vendor', 'change_vendor', 'view_vendor',
                ]
            ),
            'Vendor': Permission.objects.filter(
                codename__in=['view_rfq', 'add_quotation', 'change_quotation', 'view_quotation', 'view_purchaseorder']
            ),
            'Manager': Permission.objects.filter(
                codename__in=['view_approval', 'change_approval', 'view_rfq', 'view_quotation']
            ),
        }

        for group_name, permissions in groups_config.items():
            group, created = Group.objects.get_or_create(name=group_name)
            group.permissions.set(permissions)
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action} group: {group_name}'))

        self.stdout.write(self.style.SUCCESS('Roles and permissions configured successfully.'))
