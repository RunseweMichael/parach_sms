from django.urls import path
from . import views

urlpatterns = [
    path('completed/', views.get_completed_weeks, name='completed_weeks'),
    path('submit/', views.submit_task, name='submit_task'),
    path('skills-progress/', views.get_student_skills_progress, name='skills_progress'),
]