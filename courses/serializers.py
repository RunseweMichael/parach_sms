from rest_framework import serializers
from .models import Courses, Module, ModuleProgress, Lesson

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courses
        fields = '__all__'
        read_only_fields = ['created_at']


class ModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Module
        fields = ['id', 'title', 'order', 'course',]
        read_only_fields = ['created_at']


class ModuleProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModuleProgress
        fields = ['id', 'module', 'completed', 'completed_at']
        read_only_fields = ['id', 'completed_at']



class ModuleWithProgressSerializer(serializers.ModelSerializer):
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = ['id', 'title', 'order', 'progress']
        read_only_fields = ['created_at']

    def get_progress(self, obj):
        user = self.context['request'].user
        progress = ModuleProgress.objects.filter(user=user, module=obj).first()
        return progress.completed if progress else False


class LessonSerializer(serializers.ModelSerializer):
    module_title = serializers.CharField(source="module.title", read_only=True)

    class Meta:
        model = Lesson
        fields = ['id', 'title', 'content', 'order', 'module','course','module_title']
        read_only_fields = ['created_at']


class ModuleWithLessonsSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ['id', 'title', 'order', 'lessons']
        read_only_fields = ['created_at']


class CourseWithModulesSerializer(serializers.ModelSerializer):
    modules = ModuleWithLessonsSerializer(many=True, read_only=True)

    class Meta:
        model = Courses
        fields = ['id', 'course_name', 'price', 'modules']
        read_only_fields = ['created_at']