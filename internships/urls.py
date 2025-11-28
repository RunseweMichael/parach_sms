from rest_framework.routers import DefaultRouter
from .views import InternshipRequestViewSet

router = DefaultRouter()
router.register(r"internship-requests", InternshipRequestViewSet, basename="internshiprequest")

urlpatterns = router.urls
