from django.contrib import admin
from .models import InternshipRequest

@admin.register(InternshipRequest)
class InternshipRequestAdmin(admin.ModelAdmin):
    list_display = ("student_name", "student_email", "duration", "preferred_start_date", "is_approved", "submitted_at")
    list_filter = ("is_approved", "duration", "submitted_at")
    search_fields = ("student_name", "student_email")
    readonly_fields = ("submitted_at", "approved_at", "approved_by")
