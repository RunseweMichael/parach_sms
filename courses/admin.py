from django.contrib import admin
from .models import Courses, Module, ModuleProgress, Lesson, LessonProgress, Task, Question, Choice, TaskSubmission, TaskAnswer

# Register your models here.
admin.site.register(Courses)
admin.site.register(Module)
admin.site.register(ModuleProgress)
admin.site.register(Lesson)
admin.site.register(LessonProgress)
admin.site.register(Task)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(TaskSubmission)
admin.site.register(TaskAnswer)
