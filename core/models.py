from django.conf import settings
from django.db import models


class Notification(models.Model):
    TYPE_RFQ = 'rfq'
    TYPE_APPROVAL = 'approval'
    TYPE_INVOICE = 'invoice'
    TYPE_ACTIVITY = 'activity'
    TYPE_GENERAL = 'general'

    TYPE_CHOICES = [
        (TYPE_RFQ, 'RFQ'),
        (TYPE_APPROVAL, 'Approval'),
        (TYPE_INVOICE, 'Invoice'),
        (TYPE_ACTIVITY, 'Activity'),
        (TYPE_GENERAL, 'General'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_GENERAL)
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} - {self.user.username}'


class ActivityLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='activity_logs',
    )
    action = models.CharField(max_length=255)
    module = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        username = self.user.username if self.user else 'System'
        return f'{username}: {self.action}'
