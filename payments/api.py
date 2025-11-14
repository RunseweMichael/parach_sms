# payments/api.py
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from .models import Coupon
from .serializers import CouponSerializer

class CouponViewSet(viewsets.ModelViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAdminUser]  # Only admin users can access
    filterset_fields = ['active']  # For filter
    search_fields = ['code']
