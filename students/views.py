from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model, logout
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from .serializers import EmailAuthTokenSerializer
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from .models import EmailOTP, CustomUser
from .serializers import (
    SendOTPSerializer, VerifyOTPSerializer,
    UserRegistrationSerializer, UserProfileSerializer, SendPasswordResetOTPSerializer,
    ResetPasswordSerializer
)
from .utils import send_otp_email
from .serializers import AdminUserSerializer
from admin_panel.permissions import IsSuperAdmin, IsStaffOrSuperAdmin

User = get_user_model()

# -------------------------------
# User CRUD via ViewSet
# -------------------------------
class UserViewSet(viewsets.ModelViewSet):
    """
    Handles:
    - Registration (create)
    - Viewing and updating profile
    - Admin/staff management (promote/demote)
    """
    queryset = User.objects.all().order_by('-id')
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsAdminUser, AllowAny]
    authentication_classes = [TokenAuthentication]

    def get_permissions(self):
        """Assign permissions dynamically"""
        if self.action in ['create', 'verify_otp', 'resend_otp', 'login', 'list', 'retrieve', 'update', 'destroy']:
            return [AllowAny()]
        elif self.action in ['toggle_staff_role', 'staff_list', 'non_staff_list']:
            return [IsAuthenticated(), IsAdminUser()]
        else:
            return [IsAuthenticated()]

    # -----------------------------------------
    # 1️⃣ Register new user
    # -----------------------------------------
    def create(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        otp = EmailOTP.generate_otp(user, purpose="email_verification")
        send_otp_email(user, otp)

        return Response({"message": "User registered successfully. Check your email for OTP."},
                        status=status.HTTP_201_CREATED)

    # -----------------------------------------
    # 2️⃣ Logged-in user profile
    # -----------------------------------------
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    # -----------------------------------------
    # 3️⃣ Promote or demote staff
    # -----------------------------------------
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated, IsAdminUser])
    def toggle_staff_role(self, request):
        user_id = request.data.get("user_id")
        is_staff_admin = request.data.get("is_staff_admin")

        if user_id is None or is_staff_admin is None:
            return Response({"error": "user_id and is_staff_admin are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        user.is_staff_admin = is_staff_admin
        user.save()
        return Response({"message": f"User {'promoted' if is_staff_admin else 'demoted'} successfully."})

    # -----------------------------------------
    # 4️⃣ List staff / non-staff users
    # -----------------------------------------
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdminUser])
    def staff_list(self, request):
        staff = User.objects.filter(is_staff_admin=True)
        serializer = self.get_serializer(staff, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsAdminUser])
    def non_staff_list(self, request):
        non_staff = User.objects.filter(is_staff_admin=False, is_superadmin=False)
        serializer = self.get_serializer(non_staff, many=True)
        return Response(serializer.data)


# -------------------------------
# Send OTP
# -------------------------------
class SendOTPView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []


    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        otp = EmailOTP.generate_otp(user=user, purpose="email_verification")
        send_otp_email(user, otp)

        return Response({"message": "OTP sent successfully."})


# -------------------------------
# Verify OTP
# -------------------------------
class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        otp_obj = EmailOTP.objects.filter(user=user, code=code, is_used=False).first()
        if not otp_obj:
            return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
        if otp_obj.is_expired():
            return Response({"error": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST)

        otp_obj.mark_as_used()
        user.is_active = True
        user.save()
        return Response({"message": "OTP verified, user activated successfully"})


# -------------------------------
# Resend OTP
# -------------------------------
class ResendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)

        EmailOTP.clean_expired_otps()
        otp = EmailOTP.generate_otp(user=user, purpose='email_verification')
        send_otp_email(user, otp)

        return Response({"message": "New OTP sent successfully."})


# -------------------------------
# Custom Auth Token (Login)
# -------------------------------
class CustomAuthToken(ObtainAuthToken):
    serializer_class = EmailAuthTokenSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        if not user.is_active:
            return Response({'error': 'User is not active, please verify your email'}, status=status.HTTP_403_FORBIDDEN)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user_id': user.id, 'username': user.username})


# -------------------------------
# User Profile
# -------------------------------
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        """Allow authenticated users to update their own profile"""
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# -------------------------------
# Logout
# -------------------------------
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def post(self, request):
        request.user.auth_token.delete()
        logout(request)
        return Response({"message": "Logged out successfully"})


class SendPasswordResetOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SendPasswordResetOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Clean old OTPs and generate new
        EmailOTP.clean_expired_otps()
        otp = EmailOTP.generate_otp(user, purpose='password_reset')

        # Send email
        send_otp_email(user, otp)

        return Response({"message": "Password reset OTP sent to your email."})


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        new_password = request.data.get("new_password")

        if not all([email, otp, new_password]):
            return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # find OTP record that matches the email and code
            otp_record = EmailOTP.objects.get(user__email=email, code=otp, is_used=False)
        except EmailOTP.DoesNotExist:
            return Response({"error": "Invalid or expired OTP."}, status=status.HTTP_400_BAD_REQUEST)

        # check expiry if your model supports it
        if otp_record.is_expired():
            return Response({"error": "OTP expired."}, status=status.HTTP_400_BAD_REQUEST)

        # reset user password
        user = otp_record.user
        user.set_password(new_password)
        user.save()

        # mark OTP as used
        otp_record.is_used = True
        otp_record.save()

        return Response({"message": "Password reset successful."}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_dashboard(request):
    user = request.user
    if user.dashboard_locked:
        return Response({
            "locked": True,
            "message": "Your dashboard has been restricted due to incomplete payment. "
                       "Please pay at least 50% of your course fee to regain access."
        }, status=403)

    # normal data if not locked
    return Response({
        "locked": False,
        "course": user.course.course_name if user.course else None,
        "amount_paid": float(user.amount_paid),
        "amount_owed": float(user.amount_owed),
        "next_due_date": user.next_due_date,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def all_users(request):
    """Return all users for admin panel"""
    users = CustomUser.objects.all()
    serializer = AdminUserSerializer(users, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """Return info for currently logged-in user"""
    serializer = AdminUserSerializer(request.user)
    return Response(serializer.data)


class UserManagementViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing all users (for admin staff management)
    """
    queryset = CustomUser.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get_queryset(self):
        """Return all users, ordered by email"""
        return CustomUser.objects.all().order_by('email')
    
    @action(detail=False, methods=['get'])
    def staff_list(self, request):
        """Get list of all staff members"""
        staff_users = CustomUser.objects.filter(is_staff_admin=True)
        serializer = self.get_serializer(staff_users, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def non_staff_list(self, request):
        """Get list of non-staff users"""
        non_staff = CustomUser.objects.filter(is_staff_admin=False, is_superadmin=False)
        serializer = self.get_serializer(non_staff, many=True)
        return Response(serializer.data)












