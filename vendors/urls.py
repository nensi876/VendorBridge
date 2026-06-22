from django.urls import path
from . import views

app_name = 'vendors'

urlpatterns = [
    path('', views.vendor_list, name='list'),
    path('add/', views.vendor_create, name='create'),
    path('<int:pk>/', views.vendor_detail, name='detail'),
    path('<int:pk>/edit/', views.vendor_edit, name='edit'),
    path('<int:pk>/delete/', views.vendor_delete, name='delete'),
]
