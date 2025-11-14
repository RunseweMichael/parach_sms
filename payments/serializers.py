from rest_framework import serializers
from students.models import CustomUser
from .models import PaymentItem, Transaction, PaymentReceipt
from .models import Coupon


class UserSerializer(serializers.ModelSerializer):
    """Lightweight serializer for CustomUser."""
    class Meta:
        model = CustomUser
        fields = '__all__'
        read_only_fields = ['id', 'amount_paid', 'amount_owed', 'next_due_date']


class PaymentItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentItem
        fields = [
            'id', 'name', 'amount', 'payment_type',
            'is_active', 'is_mandatory', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PaymentReceiptSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentReceipt
        fields = ['pdf_file', 'created_at']


class TransactionSerializer(serializers.ModelSerializer):
    receipt = PaymentReceiptSerializer(read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    user_name = serializers.SerializerMethodField()
    user_course = serializers.SerializerMethodField()
    user_id = serializers.CharField(source='user.id', read_only=True)
    payment_items_details = PaymentItemSerializer(
        source='payment_items', many=True, read_only=True
    )

    def get_user_name(self, obj):
        return obj.user.name or obj.user.email

    def get_user_course(self, obj):
        return obj.user.course.course_name if obj.user.course else None

    class Meta:
        model = Transaction
        fields = [
            'id', 'reference', 'user', 'user_name', 'user_id',
            'email', 'amount', 'currency', 'status', 'channel',
            'paid_at', 'fees', 'payment_items_details','user_course',
            'refunded', 'refund_amount', 'created_at', 'updated_at', 'receipt'
        ]
        read_only_fields = ['id', 'reference', 'created_at', 'updated_at']

    def get_user_name(self, obj):
        return getattr(obj.user, 'name', obj.user.email)


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = '__all__'


