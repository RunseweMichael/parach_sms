from django.contrib import admin
from .models import CustomUser, EmailOTP

# -------------------------------
# CustomUser Admin
# -------------------------------
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'name',
        'gender',
        'is_active',
        'registration_date',
        'course',
        'amount_paid',
        'amount_owed'
    )
    search_fields = ('username', 'email', 'name')
    list_filter = ('is_active', 'gender', 'course')
    readonly_fields = ('registration_date',)

# -------------------------------
# EmailOTP Admin
# -------------------------------
@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'purpose', 'created_at', 'expires_at', 'is_used', 'attempts')
    search_fields = ('user__username', 'user__email', 'code')
    list_filter = ('is_used', 'purpose')
    readonly_fields = ('created_at', 'expires_at')
