from rest_framework import serializers
from .models import Certificate


class CertificateSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField(read_only=True)
    course_name = serializers.SerializerMethodField(read_only=True)
    certificate_file = serializers.SerializerMethodField()
    amount_owed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Certificate
        fields = [
            "id", "student", "student_name", "course", "course_name",
            "issue_date", "is_approved", "certificate_file", "certificate_number",
            'is_obsolete', 'obsolete_reason', 'obsolete_date', 'amount_owed',
        ]
        read_only_fields = ["certificate_number", "issue_date", "certificate_file"]

    def get_student_name(self, obj):
        return getattr(obj.student, "name", None) or getattr(obj.student, "username", "Unknown Student")

    def get_course_name(self, obj):
        return getattr(obj.course, "course_name", "No Course")

    def get_certificate_file(self, obj):
        if obj.certificate_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.certificate_file.url)
            return obj.certificate_file.url
        return None
    
    def get_amount_owed(self, obj):
        """Calculate the student's outstanding balance"""
        if not obj.student:
            return 0
        
        student = obj.student
        discounted_price = student.discounted_price if student.discounted_price is not None else (student.course.price if student.course else 0)
        total_paid = student.amount_paid or 0
        return float(max(0, discounted_price - total_paid))