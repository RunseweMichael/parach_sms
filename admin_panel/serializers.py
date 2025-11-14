from rest_framework import serializers
from .models import AdminActivity, Notification
from students.models import CustomUser
from courses.models import Courses
from certificates.models import Certificate
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from datetime import timedelta


class AdminActivitySerializer(serializers.ModelSerializer):
    admin_name = serializers.CharField(source='admin.username', read_only=True)
    
    class Meta:
        model = AdminActivity
        fields = ['id', 'admin', 'admin_name', 'action', 'model_name', 
                  'object_id', 'description', 'ip_address', 'timestamp']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'priority', 'is_read', 
                  'created_at', 'created_for']


class DashboardStatsSerializer(serializers.Serializer):
    """Dashboard statistics"""
    total_students = serializers.IntegerField()
    active_students = serializers.IntegerField()
    inactive_students = serializers.IntegerField()
    total_courses = serializers.IntegerField()
    total_certificates = serializers.IntegerField()
    approved_certificates = serializers.IntegerField()
    pending_certificates = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_outstanding = serializers.DecimalField(max_digits=10, decimal_places=2)
    new_students_this_month = serializers.IntegerField()
    certificates_this_month = serializers.IntegerField()


from rest_framework import serializers

class StudentStatsSerializer(serializers.Serializer):
    """Student-related statistics"""
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()
    course_name = serializers.CharField(source='course.course_name', read_only=True)
    certificate_count = serializers.SerializerMethodField()
    registration_date = serializers.DateTimeField()
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    amount_owed = serializers.DecimalField(max_digits=10, decimal_places=2)
    is_active = serializers.BooleanField()

    def get_certificate_count(self, obj):
        """Return how many certificates this student has."""
        # Adjust based on your related name
        return getattr(obj, "certificates", []).count() if hasattr(obj, "certificates") else 0


class RevenueAnalyticsSerializer(serializers.Serializer):
    """Revenue analytics"""
    month = serializers.CharField()
    total_paid = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_owed = serializers.DecimalField(max_digits=10, decimal_places=2)
    student_count = serializers.IntegerField()


class CourseStatsSerializer(serializers.Serializer):
    """Course statistics"""
    course_id = serializers.IntegerField()
    course_name = serializers.CharField()
    student_count = serializers.IntegerField()
    certificate_count = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
