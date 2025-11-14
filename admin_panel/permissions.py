from rest_framework import permissions
from rest_framework.permissions import BasePermission

class IsSuperAdmin(BasePermission):
    """Allow access only to super admins."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superadmin)

class IsStaffOrSuperAdmin(BasePermission):
    """Allow access to both super admins and staff admins."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (
            request.user.is_superadmin or request.user.is_staff_admin
        ))
