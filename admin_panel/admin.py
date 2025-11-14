from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import AdminActivity, Notification


@admin.register(AdminActivity)
class AdminActivityAdmin(admin.ModelAdmin):
    list_display = ['admin', 'action', 'model_name', 'object_id', 'timestamp', 'ip_address']
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['admin__username', 'description', 'ip_address']
    readonly_fields = ['admin', 'action', 'model_name', 'object_id', 'description', 'ip_address', 'timestamp']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'priority', 'is_read', 'created_for', 'created_at']
    list_filter = ['priority', 'is_read', 'created_at']
    search_fields = ['title', 'message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'