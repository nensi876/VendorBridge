from core.models import ActivityLog, Notification


def log_activity(user, action, module):
    ActivityLog.objects.create(user=user, action=action, module=module)


def create_notification(user, title, message, notification_type=Notification.TYPE_GENERAL, link=''):
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link,
    )


def notify_role(role, title, message, notification_type=Notification.TYPE_GENERAL, link=''):
    from accounts.models import User
    users = User.objects.filter(role=role, is_active=True)
    for user in users:
        create_notification(user, title, message, notification_type, link)
