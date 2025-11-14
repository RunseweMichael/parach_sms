from rest_framework import viewsets
from .models import Courses, Module, Lesson
from .serializers import CourseSerializer, ModuleSerializer, LessonSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Courses.objects.prefetch_related('modules__lessons').all().order_by('-created_at')
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]
    def get_serializer_class(self):
        if self.action == 'retrieve':
            from .serializers import CourseWithModulesSerializer
            return CourseWithModulesSerializer
        return CourseSerializer
        
    def get_permissions(self):
        if self.action == "list" or self.action == "retrieve":
            return [AllowAny()]
        return [IsAuthenticated()]


class ModuleViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Module.objects.all().order_by('order')
    serializer_class = ModuleSerializer


class LessonViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = Lesson.objects.all().order_by('order')
    serializer_class = LessonSerializer
