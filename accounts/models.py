from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_ADMIN = 'admin'
    ROLE_PROCUREMENT = 'procurement_officer'
    ROLE_VENDOR = 'vendor'
    ROLE_MANAGER = 'manager'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_PROCUREMENT, 'Procurement Officer'),
        (ROLE_VENDOR, 'Vendor'),
        (ROLE_MANAGER, 'Manager / Approver'),
    ]

    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default=ROLE_PROCUREMENT)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['username']

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    @property
    def is_admin_role(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    @property
    def is_procurement_officer(self):
        return self.role == self.ROLE_PROCUREMENT

    @property
    def is_vendor_role(self):
        return self.role == self.ROLE_VENDOR

    @property
    def is_manager_role(self):
        return self.role == self.ROLE_MANAGER

    def get_dashboard_redirect(self):
        if self.is_vendor_role:
            return 'procurement:vendor_rfq_list'
        return 'core:dashboard'
