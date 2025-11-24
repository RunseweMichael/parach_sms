from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import EmailOTP, CustomUser
from certificates.models import Certificate
from certificates.serializers import CertificateSerializer
from courses.models import Courses
from courses.serializers import CourseSerializer
from django.contrib.auth import authenticate
User = get_user_model()


# -------------------------------
# OTP SERIALIZERS
# -------------------------------
class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        User = get_user_model()
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No user with this email address.")
        return value


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must be numeric.")
        if len(value) != 6:
            raise serializers.ValidationError("OTP must be exactly 6 digits.")
        return value


# -------------------------------
# USER REGISTRATION SERIALIZER
# -------------------------------
class UserRegistrationSerializer(serializers.ModelSerializer):
    course = serializers.PrimaryKeyRelatedField(queryset=Courses.objects.all(), required=True)
    certificates = CertificateSerializer(many=True, read_only=True)
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False, read_only=True)
    amount_owed = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False, read_only=True)
    password = serializers.CharField(write_only=True)
    center = serializers.ChoiceField(choices=CustomUser.CENTER_CHOICES, required=True)
    course_name = serializers.CharField(source='course.course_name', read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id", "username", "email", "name", "gender", "birth_date",
            "phone_number", "address", "consent", "registration_date",
            "amount_paid", "amount_owed", "next_due_date", "is_active",
            "course", "certificates", "password", "course_name","center"
        ]
        extra_kwargs = {"username": {"required": False, "allow_blank": True}}

    def create(self, validated_data):
        user = CustomUser(
            username=validated_data.get('username', ''),
            email=validated_data['email'],
            name=validated_data.get('name'),
            gender=validated_data.get('gender'),
            course=validated_data.get('course'),
            birth_date=validated_data.get('birth_date'),
            phone_number=validated_data.get('phone_number'),
            center=validated_data.get('center'),
            address=validated_data.get('address'),
            consent=validated_data.get('consent', False),
        )
        user.set_password(validated_data['password'])
        user.save()

        # Automatically create a certificate entry
        if user.course:
            Certificate.objects.create(student=user, course=user.course, is_approved=False)

        return user


# -------------------------------
# USER PROFILE SERIALIZER
# -------------------------------
class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user management including staff roles"""
    certificates = CertificateSerializer(many=True, read_only=True)
    course = CourseSerializer(read_only=True)
    course_name = serializers.CharField(source='course.course_name', read_only=True)
    amount_owed = serializers.SerializerMethodField()
    center = serializers.ChoiceField(choices=CustomUser.CENTER_CHOICES)
    amount_paid = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)

    
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'email',
            'username',
            'name',
            'gender',
            'consent',
            'phone_number',
            'address',
            'birth_date',
            'course',
            'center',
            'course_name',
            'amount_paid',
            'amount_owed',
            'next_due_date',
            'is_active',
            'is_staff',
            'is_staff_admin',  # ✅ Include this
            'is_superadmin',
            'registration_date',
            'discounted_price',
            'certificates',
        ]
        read_only_fields = [
            'id',
            'registration_date',
            'amount_owed',
        ]
        
    def get_amount_owed(self, obj):
        discounted_price = obj.discounted_price if obj.discounted_price is not None else (obj.course.price if obj.course else 0)
        total_paid = obj.amount_paid or 0
        return float(max(0, discounted_price - total_paid))

    def validate_email(self, value):
        user = self.instance
        qs = CustomUser.objects.filter(email=value)
        if user:
            qs = qs.exclude(pk=user.pk)
        if qs.exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value
    
    def to_representation(self, instance):
        """Ensure boolean fields are properly serialized"""
        data = super().to_representation(instance)
        # Ensure these are actual booleans, not strings
        data['is_staff_admin'] = bool(instance.is_staff_admin)
        data['is_staff'] = bool(instance.is_staff)
        data['is_superadmin'] = bool(instance.is_superadmin)
        data['is_active'] = bool(instance.is_active)
        return data


class UserProfileDetailSerializer(serializers.ModelSerializer):
    """Detailed user serializer for profile/me endpoint"""
    
    course = serializers.SerializerMethodField()
    
    def get_course(self, obj):
        if obj.course:
            return {
                'id': obj.course.id,
                'course_name': obj.course.course_name,
                'price': float(obj.course.price) if obj.course.price else 0,
            }
        return None
    
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'email',
            'username',
            'name',
            'gender',
            'phone_number',
            'address',
            'birth_date',
            'course',
            'amount_paid',
            'amount_owed',
            'next_due_date',
            'dashboard_locked',
            'is_active',
            'is_staff_admin',
            'is_superadmin',
            'registration_date',
        ]
        read_only_fields = ['id', 'registration_date']


class EmailAuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password")

        user = authenticate(email=email, password=password)
        if user is None:
            raise serializers.ValidationError("Invalid email or password")
        attrs['user'] = user
        return attrs


class SendPasswordResetOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(min_length=8)

    def post(self, request):
        serializer = self.ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp']
        new_password = serializer.validated_data['new_password']

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        otp_obj = EmailOTP.objects.filter(user=user, code=otp_code, purpose='password_reset', is_used=False).first()
        if not otp_obj or otp_obj.is_expired():
            return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)

        otp_obj.mark_as_used()
        user.set_password(new_password)
        user.save()

        return Response({"message": "Password reset successful."})


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'username',
            'email',
            'is_staff_admin',  # this is required for your toggle button
            'is_superadmin',   # optional if you want to show superadmin status
        ]
