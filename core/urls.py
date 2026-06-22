from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('activity/', views.activity_log_list, name='activity_log'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('reports/', views.reports, name='reports'),
    path('reports/export/', views.export_reports_csv, name='export_reports'),
]
