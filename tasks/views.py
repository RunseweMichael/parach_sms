# tasks/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import TaskSubmission
from students.models import CustomUser as Student
import json

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_completed_weeks(request):
    """Get all completed weeks for the current student with scores"""
    student = request.user
    
    submissions = TaskSubmission.objects.filter(
        student=student
    ).values('week_id', 'module_id', 'course_id', 'percentage')
    
    completed_data = []
    for submission in submissions:
        completed_data.append({
            'week_id': submission['week_id'],
            'module_id': submission['module_id'],
            'course_id': submission['course_id'],
            'percentage': submission['percentage']
        })
    
    return Response(completed_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_task(request):
    """Submit task answers and calculate score"""
    student = request.user
    data = request.data
    
    week_id = data.get('week_id')
    module_id = data.get('module_id')
    module_name = data.get('module_name', '')
    course_id = data.get('course_id')
    answers = data.get('answers', {})
    score = data.get('score', {})
    
    print(f"Submitting task for student: {student.email}")
    print(f"Module: {module_name}, Week: {week_id}, Score: {score.get('percentage')}%")
    
    # Save or update submission - ONLY ONE update_or_create call
    submission, created = TaskSubmission.objects.update_or_create(
        student=student,
        week_id=week_id,
        defaults={
            'course_id': course_id,
            'module_id': module_id,
            'module_name': module_name,
            'answers': json.dumps(answers),  # Convert dict to JSON string
            'correct_count': score.get('correct', 0),
            'total_questions': score.get('total', 0),
            'percentage': score.get('percentage', 0),
        }
    )
    
    print(f"Submission {'created' if created else 'updated'}: {submission}")
    
    return Response({
        'success': True,
        'message': 'Task submitted successfully',
        'score': score
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_student_skills_progress(request):
    """Get student's skills progress based on module completion"""
    student = request.user
    
    print(f"Fetching skills for student: {student.email}")
    
    # Get all submissions for the student
    submissions = TaskSubmission.objects.filter(student=student)
    
    print(f"Found {submissions.count()} submissions")
    
    # Group by module and calculate average
    module_stats = {}
    
    for submission in submissions:
        module_id = submission.module_id
        
        print(f"Processing submission - Module: {submission.module_name}, Score: {submission.percentage}%")
        
        if module_id not in module_stats:
            module_stats[module_id] = {
                'module_id': module_id,
                'module_name': submission.module_name or f"Module {module_id}",
                'scores': [],
                'completed_weeks': 0
            }
        
        module_stats[module_id]['scores'].append(submission.percentage)
        module_stats[module_id]['completed_weeks'] += 1
    
    # Calculate average for each module
    skills_data = []
    for module_id, stats in module_stats.items():
        avg_score = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0
        skills_data.append({
            'module_name': stats['module_name'],
            'average_score': round(avg_score, 1),
            'completed_weeks': stats['completed_weeks'],
            'total_score': sum(stats['scores'])
        })
    
    print(f"Returning skills data: {skills_data}")
    
    return Response(skills_data)