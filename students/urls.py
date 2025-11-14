from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SendOTPView, VerifyOTPView, ResendOTPView,
    UserViewSet, CustomAuthToken, UserProfileView, LogoutView, SendPasswordResetOTPView, ResetPasswordView
)
from . import views

# DRF router for user CRUD (registration, list, retrieve, update, delete)
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')


urlpatterns = [
    # OTP endpoints
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),

    # Authentication
    path('login/', CustomAuthToken.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # User profile
    path('me/', UserProfileView.as_view(), name='user-profile'),
    

    # Password Reset
    path('send-reset-otp/', SendPasswordResetOTPView.as_view(), name='send-password-reset-otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),

    # User CRUD via router
    path('', include(router.urls)),
]
