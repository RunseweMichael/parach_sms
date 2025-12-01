from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def home(request):
    return JsonResponse({"message": "Parach ICT Academy API is running."})

urlpatterns = [
    path('', home),
    path('admin/', admin.site.urls),

    path('api/students/', include(('students.urls', 'students'), namespace='students')),
    path('api/courses/', include(('courses.urls', 'courses'), namespace='courses')),
    path('api/enquiries/', include(('enquiries.urls', 'enquiries'), namespace='enquiries')),
    path('api/certificates/', include(('certificates.urls', 'certificates'), namespace='certificates')),
    path('api/admin-panel/', include('admin_panel.urls')),
    path('api/payments/', include('payments.urls')),
    path("api/", include("internships.urls")),
    path('api/tasks/', include(('tasks.urls', 'tasks'), namespace='tasks')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)