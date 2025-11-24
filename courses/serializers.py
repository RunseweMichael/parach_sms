from rest_framework import serializers
from .models import Courses, Module, ModuleProgress, Lesson, Choice, Question, TaskAnswer, TaskSubmission, Task

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


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ['id', 'choice_text']



class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'question_text', 'choices']



class TaskSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Task
        fields = '__all__'



class LessonSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)
    module_title = serializers.CharField(source="module.title", read_only=True)

    class Meta:
        model = Lesson
        fields = '__all__'
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










# serializers.py
from rest_framework import serializers
from .models import Task, Question, Choice, TaskSubmission, TaskAnswer







# Submission serializers
class TaskAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskAnswer
        fields = ['question', 'selected_choice']

class TaskSubmissionSerializer(serializers.ModelSerializer):
    answers = TaskAnswerSerializer(many=True)
    score = serializers.FloatField(read_only=True)
    completed = serializers.BooleanField(read_only=True)
    correct_answers = serializers.SerializerMethodField()

    class Meta:
        model = TaskSubmission
        fields = [
            'id', 'task', 'user', 'submitted_at',
            'score', 'completed', 'answers', 'correct_answers'
        ]

    def get_correct_answers(self, obj):
        """Return {question_id: correct_choice_id}"""
        correct_map = {}
        for question in obj.task.questions.all():
            correct_choice = question.choices.filter(is_correct=True).first()
            if correct_choice:
                correct_map[question.id] = correct_choice.id
        return correct_map

    def create(self, validated_data):
        answers_data = validated_data.pop('answers')
        submission = TaskSubmission.objects.create(**validated_data)
        correct_count = 0

        for ans_data in answers_data:
            question = ans_data['question']
            choice = ans_data['selected_choice']

            TaskAnswer.objects.create(
                submission=submission,
                question=question,
                selected_choice=choice
            )

            if choice.is_correct:
                correct_count += 1

        total_questions = submission.task.questions.count()
        submission.score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        submission.completed = True
        submission.save()

        return submission

