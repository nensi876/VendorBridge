from django.conf import settings
from django.db import models


class Vendor(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_INACTIVE, 'Inactive'),
    ]

    CATEGORY_CHOICES = [
        ('it', 'IT & Software'),
        ('office', 'Office Supplies'),
        ('manufacturing', 'Manufacturing'),
        ('services', 'Professional Services'),
        ('logistics', 'Logistics'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vendor_profile',
    )
    vendor_name = models.CharField(max_length=150)
    company_name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    gst_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['company_name']

    def __str__(self):
        return self.company_name
