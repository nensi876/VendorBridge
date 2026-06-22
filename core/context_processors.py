def notifications_processor(request):
    if request.user.is_authenticated:
        unread = request.user.notifications.filter(is_read=False).count()
        recent = request.user.notifications.all()[:5]
        return {'unread_notifications': unread, 'recent_notifications': recent}
    return {'unread_notifications': 0, 'recent_notifications': []}
