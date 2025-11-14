from django_filters import rest_framework as filters
from students.models import CustomUser
from certificates.models import Certificate
from .models import AdminActivity


class StudentFilter(filters.FilterSet):
    """Filter for student queries"""
    is_active = filters.BooleanFilter()
    course = filters.NumberFilter(field_name='course__id')
    registration_date_from = filters.DateFilter(field_name='registration_date', lookup_expr='gte')
    registration_date_to = filters.DateFilter(field_name='registration_date', lookup_expr='lte')
    has_outstanding = filters.BooleanFilter(method='filter_has_outstanding')
    
    class Meta:
        model = CustomUser
        fields = ['is_active', 'course', 'consent']
    
    def filter_has_outstanding(self, queryset, name, value):
        if value:
            return queryset.filter(amount_owed__gt=0)
        return queryset.filter(amount_owed=0)


class CertificateFilter(filters.FilterSet):
    """Filter for certificate queries"""
    is_approved = filters.BooleanFilter()
    student = filters.NumberFilter(field_name='student__id')
    course = filters.NumberFilter(field_name='course__id')
    issue_date_from = filters.DateFilter(field_name='issue_date', lookup_expr='gte')
    issue_date_to = filters.DateFilter(field_name='issue_date', lookup_expr='lte')
    
    class Meta:
        model = Certificate
        fields = ['is_approved', 'student', 'course']


class AdminActivityFilter(filters.FilterSet):
    """Filter for admin activity logs"""
    action = filters.ChoiceFilter(choices=AdminActivity.ACTION_CHOICES)
    admin = filters.NumberFilter(field_name='admin__id')
    model_name = filters.CharFilter(lookup_expr='icontains')
    timestamp_from = filters.DateTimeFilter(field_name='timestamp', lookup_expr='gte')
    timestamp_to = filters.DateTimeFilter(field_name='timestamp', lookup_expr='lte')
    
    class Meta:
        model = AdminActivity
        fields = ['action', 'admin', 'model_name']