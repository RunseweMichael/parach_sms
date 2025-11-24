from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DashboardViewSet,
    AdminActivityViewSet,
    NotificationViewSet,
    StudentManagementViewSet,
    export_data,
    toggle_staff_role,
    notify_defaulters,
)
from . import views

router = DefaultRouter()
router.register(r'dashboard', DashboardViewSet, basename='dashboard')
router.register(r'activities', AdminActivityViewSet, basename='activities')
router.register(r'notifications', NotificationViewSet, basename='notifications')
router.register(r'students', StudentManagementViewSet, basename='admin-students')

urlpatterns = [
    path('', include(router.urls)),
    path('export/', export_data, name='export-data'),
    path('toggle-staff-role/', toggle_staff_role, name='toggle-staff-role'),
    path('paginated-users/', views.paginated_users, name='paginated-users'),
    path("notify_defaulters/", notify_defaulters, name="notify_defaulters"),
]