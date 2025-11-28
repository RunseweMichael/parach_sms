from rest_framework import serializers
from .models import InternshipRequest

class InternshipRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = InternshipRequest
        # Expose all fields; admin-only fields are read-only
        fields = "__all__"
        read_only_fields = ("is_approved", "approved_at", "approved_by", "internship_pdf", "submitted_at")
