# tasks/models.py
from django.db import models
from students.models import CustomUser as Student

class TaskSubmission(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='task_submissions')
    course_id = models.IntegerField()
    module_id = models.IntegerField()
    module_name = models.CharField(max_length=200, blank=True, null=True)
    week_id = models.IntegerField()
    answers = models.TextField(default="{}")
    correct_count = models.IntegerField(default=0)
    total_questions = models.IntegerField(default=0)
    percentage = models.FloatField(default=0)
    submitted_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'week_id']
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.student.email} - Week {self.week_id} - {self.percentage}%"