from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .api import CouponViewSet

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='users')
router.register(r'payment-items', views.PaymentItemViewSet, basename='payment-items')
router.register(r'transactions', views.TransactionViewSet, basename='transactions')
router.register(r'coupons', CouponViewSet, basename='coupons')


urlpatterns = [
    path('', include(router.urls)),
    
    path('initialize/', views.initialize_payment, name='initialize_payment'),
    path('verify/<str:reference>/', views.verify_payment, name='verify_payment'),
    path('webhook/', views.paystack_webhook, name='paystack_webhook'),
    path('statistics/', views.payment_statistics, name='payment_statistics'),
    path('get_balance/', views.get_balance, name='get_balance'),
    path('student-transactions/', views.StudentTransactionListView.as_view(), name='student-transactions'),   
    path('download/<str:reference>/', views.download_receipt, name='download_receipt'),
]
