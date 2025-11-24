from rest_framework import viewsets
from .models import Courses, Module, Lesson
from .serializers import CourseSerializer, ModuleSerializer, LessonSerializer, TaskSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import generics, permissions
from .models import Task, TaskSubmission
from .serializers import TaskSerializer, TaskSubmissionSerializer


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


# Get tasks for a lesson
class TaskListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        lesson_id = self.kwargs['lesson_id']
        return Task.objects.filter(lesson_id=lesson_id).order_by('order')


# Submit a task
class TaskSubmissionView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskSubmissionSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# Optional: List submissions for a student
class TaskSubmissionListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskSubmissionSerializer

    def get_queryset(self):
        return TaskSubmission.objects.filter(user=self.request.user)



class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer

    def get_queryset(self):
        qs = Task.objects.all()
        lesson_id = self.request.query_params.get("lesson")
        if lesson_id:
            qs = qs.filter(lesson_id=lesson_id)
        return qs

