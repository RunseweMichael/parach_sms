from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

class Courses(models.Model):
    course_name = models.CharField(max_length=100, blank=False, null=False, unique = True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=False, null=False)
    duration = models.IntegerField(blank=False, null=False)
    skills = models.TextField(blank=True, null=True)
    status = models.BooleanField(default=True)
    resource_link = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    def __str__(self):
        return self.course_name


class Module(models.Model):
    course = models.ForeignKey(Courses, related_name='modules', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField()  # to specify sequence
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        unique_together = ('course', 'order')

    def __str__(self):
        return f"{self.course.course_name} - {self.title}"


class ModuleProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'module')
        verbose_name = "Module Progress"
    
    def __str__(self):
        return f"{self.user.username} - {self.module.title} ({'Done' if self.completed else 'Pending'})"


class Lesson(models.Model):
    course = models.ForeignKey(Courses, related_name='lessons', on_delete=models.CASCADE, null = True)
    module = models.ForeignKey(Module, related_name='lessons', on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True, null=True)
    content = models.TextField(blank=True, null=True)  # could be text, HTML, or markdown
    order = models.PositiveIntegerField(blank=True, null=True)  # sequence in the module
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']  # ensures lessons appear in order

    def __str__(self):
        return f"{self.module.title} - {self.title}"


class LessonProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'lesson')
        ordering = ['lesson__order']
        verbose_name = "Lesson Progress"

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title} ({'Done' if self.completed else 'Pending'})"

    
