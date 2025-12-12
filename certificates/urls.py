# certificates/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import CertificateViewSet, verify_certificate

router = DefaultRouter()
router.register("certificates", CertificateViewSet, basename="certificate")

urlpatterns = [
    *router.urls,

    path("verify-certificate/", verify_certificate, name="verify-certificate"),
]
