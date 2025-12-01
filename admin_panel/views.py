from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db.models import Count, Sum, Q, Avg, F
from django.utils import timezone
from .permissions import IsSuperAdmin, IsStaffOrSuperAdmin
from rest_framework.pagination import PageNumberPagination
from students.serializers import UserProfileSerializer
from django.contrib.auth import get_user_model
from .notifications import format_phone_number
from datetime import timedelta, datetime
from .models import AdminActivity, Notification
from .serializers import (
    AdminActivitySerializer, NotificationSerializer,
    DashboardStatsSerializer, StudentStatsSerializer,
    RevenueAnalyticsSerializer, CourseStatsSerializer
)
from students.models import CustomUser
from courses.models import Courses
from certificates.models import Certificate
import logging


logger = logging.getLogger(__name__)


def log_admin_activity(admin, action, model_name, object_id=None, description="", ip_address=None):
    """Helper function to log admin activities"""
    try:
        AdminActivity.objects.create(
            admin=admin,
            action=action,
            model_name=model_name,
            object_id=object_id,
            description=description,
            ip_address=ip_address
        )
    except Exception as e:
        logger.error(f"Failed to log admin activity: {str(e)}")


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class DashboardViewSet(viewsets.ViewSet):
    """Dashboard statistics and analytics"""
    permission_classes = [IsAuthenticated, IsStaffOrSuperAdmin]
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get overall dashboard statistics"""
        try:
            # Student stats
            students = CustomUser.objects.filter(is_staff=False)
            total_students = students.count()
            active_students = students.filter(is_active=True).count()
            inactive_students = total_students - active_students
            
            # Course stats
            total_courses = Courses.objects.count()
            
            # Certificate stats
            certificates = Certificate.objects.all()
            total_certificates = certificates.count()
            approved_certificates = certificates.filter(is_approved=True).count()
            pending_certificates = total_certificates - approved_certificates
            
            # Financial stats
            financial_data = students.aggregate(
                total_revenue=Sum('amount_paid'),
                total_outstanding=Sum('amount_owed')
            )
            
            # This month stats
            current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            new_students_this_month = students.filter(
                registration_date__gte=current_month
            ).count()
            
            certificates_this_month = certificates.filter(
                issue_date__gte=current_month
            ).count()
            
            stats_data = {
                'total_students': total_students,
                'active_students': active_students,
                'inactive_students': inactive_students,
                'total_courses': total_courses,
                'total_certificates': total_certificates,
                'approved_certificates': approved_certificates,
                'pending_certificates': pending_certificates,
                'total_revenue': financial_data['total_revenue'] or 0,
                'total_outstanding': financial_data['total_outstanding'] or 0,
                'new_students_this_month': new_students_this_month,
                'certificates_this_month': certificates_this_month,
            }
            
            serializer = DashboardStatsSerializer(stats_data)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Dashboard stats error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def recent_students(self, request):
        """Get recently registered students"""
        try:
            limit = int(request.query_params.get('limit', 10))
            students = CustomUser.objects.filter(
                is_staff=False
            ).order_by('-registration_date')[:limit]
            
            data = StudentStatsSerializer(students, many=True).data
            return Response(data)
            
        except Exception as e:
            logger.error(f"Recent students error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def revenue_analytics(self, request):
        """Get revenue analytics by month"""
        try:
            months = int(request.query_params.get('months', 6))
            
            # Get data for last N months
            end_date = timezone.now()
            start_date = end_date - timedelta(days=30 * months)
            
            students = CustomUser.objects.filter(
                is_staff=False,
                registration_date__gte=start_date
            )
            
            # Group by month
            monthly_data = []
            for i in range(months):
                month_start = end_date - timedelta(days=30 * (i + 1))
                month_end = end_date - timedelta(days=30 * i)
                
                month_students = students.filter(
                    registration_date__gte=month_start,
                    registration_date__lt=month_end
                )
                
                aggregates = month_students.aggregate(
                    total_paid=Sum('amount_paid'),
                    total_owed=Sum('amount_owed'),
                    student_count=Count('id')
                )
                
                monthly_data.append({
                    'month': month_start.strftime('%b %Y'),
                    'total_paid': aggregates['total_paid'] or 0,
                    'total_owed': aggregates['total_owed'] or 0,
                    'student_count': aggregates['student_count']
                })
            
            serializer = RevenueAnalyticsSerializer(monthly_data, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Revenue analytics error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def course_stats(self, request):
        """Get statistics for each course"""
        try:
            courses = Courses.objects.annotate(
                student_count=Count('customuser', filter=Q(customuser__is_staff=False)),
                certificate_count=Count('certificate'),
                total_revenue=Sum('customuser__amount_paid', filter=Q(customuser__is_staff=False))
            ).values('id', 'course_name', 'student_count', 'certificate_count', 'total_revenue')
            
            course_data = [{
                'course_id': course['id'],
                'course_name': course['course_name'],
                'student_count': course['student_count'] or 0,
                'certificate_count': course['certificate_count'] or 0,
                'total_revenue': course['total_revenue'] or 0
            } for course in courses]
            
            serializer = CourseStatsSerializer(course_data, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Course stats error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """View admin activity logs"""
    queryset = AdminActivity.objects.all()
    serializer_class = AdminActivitySerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def get_queryset(self):
        queryset = AdminActivity.objects.all()
        
        # Filter by action
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        return queryset


class NotificationViewSet(viewsets.ModelViewSet):
    """Manage notifications"""
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated, IsStaffOrSuperAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Notification.objects.filter(
                Q(created_for=user) | Q(created_for__isnull=True)
            )
        return Notification.objects.none()
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'message': 'Notification marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        self.get_queryset().update(is_read=True)
        return Response({'message': 'All notifications marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'count': count})


class StudentManagementViewSet(viewsets.ModelViewSet):
    """Enhanced student management with admin features"""
    permission_classes = [IsAuthenticated, IsStaffOrSuperAdmin]
    
    def get_queryset(self):
        return CustomUser.objects.filter(is_staff=False).select_related('course')
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle student active status"""
        try:
            student = self.get_object()
            student.is_active = not student.is_active
            student.save()
            
            # Log activity
            log_admin_activity(
                admin=request.user,
                action='UPDATE',
                model_name='Student',
                object_id=student.id,
                description=f"{'Activated' if student.is_active else 'Deactivated'} student {student.username}",
                ip_address=get_client_ip(request)
            )
            
            return Response({
                'message': f"Student {'activated' if student.is_active else 'deactivated'} successfully",
                'is_active': student.is_active
            })
            
        except Exception as e:
            logger.error(f"Toggle active error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def update_payment(self, request, pk=None):
        """Update student payment information (robust, with logging and validation)"""
        try:
            student = self.get_object()
            data = request.data

            # Log incoming payload for debugging
            logger.info(f"update_payment called for student {student.id} by {request.user}. payload: {data}")

            # Extract values
            amount_paid = data.get('amount_paid', None)
            amount_owed = data.get('amount_owed', None)
            next_due_date = data.get('next_due_date', None)  # expect ISO 'YYYY-MM-DD' or empty/null

            # Validate & cast numeric values safely
            def safe_float(val, field_name):
                if val is None or val == "":
                    return None
                try:
                    return float(val)
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid numeric value for {field_name}: {val}")

            if amount_paid is not None:
                amount_paid_val = safe_float(amount_paid, 'amount_paid')
                student.amount_paid = amount_paid_val

            if amount_owed is not None:
                amount_owed_val = safe_float(amount_owed, 'amount_owed')
                student.amount_owed = amount_owed_val

            # ✅ Handle date parsing properly
            if next_due_date is not None:
                if next_due_date == "" or next_due_date is False:
                    student.next_due_date = None
                else:
                    try:
                        # Convert string (e.g. "2025-11-08") to a real date object
                        parsed_date = datetime.strptime(next_due_date, "%Y-%m-%d").date()
                        student.next_due_date = parsed_date
                    except ValueError:
                        return Response(
                            {"error": f"Invalid date format for next_due_date: '{next_due_date}'. Expected 'YYYY-MM-DD'."},
                            status=status.HTTP_400_BAD_REQUEST
                        )

            student.save()

            # Log admin activity
            log_admin_activity(
                admin=request.user,
                action='UPDATE',
                model_name='Student',
                object_id=student.id,
                description=f"Updated payment info for {student.username}",
                ip_address=get_client_ip(request)
            )

            return Response({
                'message': 'Payment information updated successfully',
                'amount_paid': student.amount_paid,
                'amount_owed': student.amount_owed,
                'next_due_date': student.next_due_date
            })

        except ValueError as ve:
            logger.warning(f"Validation error updating payment for {pk}: {ve}")
            return Response({'error': str(ve)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.exception(f"Update payment failed for student {pk}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    
    @action(detail=False, methods=['get'])
    def defaulters(self, request):
        """Get list of students with outstanding payments"""
        try:
            defaulters = self.get_queryset().filter(
                amount_owed__gt=0
            ).order_by('-amount_owed')
            
            data = StudentStatsSerializer(defaulters, many=True).data
            return Response(data)
            
        except Exception as e:
            logger.error(f"Defaulters error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def bulk_activate(self, request):
        """Bulk activate students"""
        try:
            student_ids = request.data.get('student_ids', [])
            
            updated = CustomUser.objects.filter(
                id__in=student_ids,
                is_staff=False
            ).update(is_active=True)
            
            # Log activity
            log_admin_activity(
                admin=request.user,
                action='UPDATE',
                model_name='Student',
                description=f"Bulk activated {updated} students",
                ip_address=get_client_ip(request)
            )
            
            return Response({
                'message': f'{updated} students activated successfully'
            })
            
        except Exception as e:
            logger.error(f"Bulk activate error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def bulk_deactivate(self, request):
        """Bulk deactivate students"""
        try:
            student_ids = request.data.get('student_ids', [])
            
            updated = CustomUser.objects.filter(
                id__in=student_ids,
                is_staff=False
            ).update(is_active=False)
            
            # Log activity
            log_admin_activity(
                admin=request.user,
                action='UPDATE',
                model_name='Student',
                description=f"Bulk deactivated {updated} students",
                ip_address=get_client_ip(request)
            )
            
            return Response({
                'message': f'{updated} students deactivated successfully'
            })
            
        except Exception as e:
            logger.error(f"Bulk deactivate error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def export_data(request):
    """Export data to CSV"""
    try:
        import csv
        from django.http import HttpResponse
        
        export_type = request.data.get('type', 'students')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{export_type}_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        
        if export_type == 'students':
            writer.writerow([
                'ID', 'Username', 'Email', 'Course', 'Phone', 'Address',
                'Amount Paid', 'Amount Owed', 'Next Due Date', 'Active',
                'Registration Date'
            ])
            
            students = CustomUser.objects.filter(is_staff=False).select_related('course')
            for student in students:
                writer.writerow([
                    student.id,
                    student.username,
                    student.email,
                    student.course.course_name if student.course else 'N/A',
                    student.phone_number or '',
                    student.address or '',
                    student.amount_paid or 0,
                    student.amount_owed or 0,
                    student.next_due_date or '',
                    'Yes' if student.is_active else 'No',
                    student.registration_date.strftime('%Y-%m-%d')
                ])
        
        elif export_type == 'certificates':
            writer.writerow([
                'ID', 'Student', 'Course', 'Certificate Number',
                'Issue Date', 'Approved', 'File'
            ])
            
            certificates = Certificate.objects.all().select_related('student', 'course')
            for cert in certificates:
                writer.writerow([
                    cert.id,
                    cert.student.username,
                    cert.course.course_name if cert.course else 'N/A',
                    cert.certificate_number,
                    cert.issue_date.strftime('%Y-%m-%d'),
                    'Yes' if cert.is_approved else 'No',
                    cert.certificate_file.url if cert.certificate_file else ''
                ])
        
        # Log activity
        log_admin_activity(
            admin=request.user,
            action='CREATE',
            model_name='Export',
            description=f"Exported {export_type} data",
            ip_address=get_client_ip(request)
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



@api_view(['POST'])
@permission_classes([IsAdminUser])
def toggle_staff_role(request):
    """Toggle is_staff_admin for a user"""
    user_id = request.data.get('user_id')
    is_staff_admin = request.data.get('is_staff_admin')

    if user_id is None or is_staff_admin is None:
        return Response({"error": "user_id and is_staff_admin are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    # Update both is_staff_admin and is_staff for Django permission purposes
    user.is_staff_admin = is_staff_admin
    user.is_staff = is_staff_admin
    user.save(update_fields=['is_staff_admin', 'is_staff'])

    role_status = "promoted to staff" if is_staff_admin else "demoted from staff"
    return Response({"message": f"{user.email} has been {role_status}."}, status=status.HTTP_200_OK)




@api_view(['GET'])
@permission_classes([IsAdminUser])
def paginated_users(request):
    search = request.GET.get('search', '')
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 20)
    is_staff_admin = request.GET.get('is_staff_admin')  # optional filter

    users = CustomUser.objects.all().order_by('-is_staff')

    # 🔍 Optional: Search by name or email
    if search:
        users = users.filter(Q(name__icontains=search) | Q(email__icontains=search))

    # 🔎 Optional: Filter by staff status
    if is_staff_admin in ['true', 'false']:
        users = users.filter(is_staff_admin=(is_staff_admin == 'true'))

    # 📄 Pagination
    paginator = PageNumberPagination()
    paginator.page_size = per_page
    result_page = paginator.paginate_queryset(users, request)
    serializer = UserProfileSerializer(result_page, many=True)

    return paginator.get_paginated_response(serializer.data)




User = get_user_model()

# @api_view(["POST"])
# @permission_classes([IsAdminUser])
# def notify_defaulters(request):
#     student_ids = request.data.get("student_ids", [])
#     if not student_ids:
#         return Response({"error": "No students selected"}, status=400)

#     students = User.objects.filter(id__in=student_ids, is_active=True)
#     failed = []

#     for student in students:
#         if not student.phone_number:
#             failed.append(f"{student.name} (No phone number)")
#             continue

#         phone = format_phone_number(student.phone_number)
#         due_date = student.next_due_date.strftime("%Y-%m-%d") if student.next_due_date else "N/A"

#         # Branded message
#         message = (
#             f"🏢 *Parach ICT Academy.*\n\n" 
#             f"Hello {student.name},\n"
#             f"💰 You have an outstanding payment of *₦{student.amount_owed:.2f}*.\n"
#             f"📅 Please pay by *{due_date}*.\n\n"
#             "For assistance, reply to this message or visit our website: https://https://parachictacademy.com.ng/\n"
#             "✅ Thank you for being part of Parach Academy!"
#         )

#         success, result = send_whatsapp_message(phone, message)
#         if not success:
#             failed.append(f"{student.name} ({result})")

#     if failed:
#         return Response({"message": "Some notifications failed", "failed": failed})
    
#     return Response({"message": f"Notifications sent to {students.count() - len(failed)} students"})













import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from students.models import CustomUser as Student

TERMII_API_KEY = settings.TERMII_API_KEY
TERMII_BASE_URL = settings.TERMII_BASE_URL


def normalize_phone(number):
    """Convert phone number to international format (Nigeria example)."""
    if not number:
        return None
    number = number.strip().replace(" ", "")
    if number.startswith("0"):
        number = "234" + number[1:]
    elif number.startswith("+"):
        number = number[1:]
    return f"+{number}"


def send_whatsapp_message(phone, message):
    """
    Send WhatsApp message using Termii.
    """
    payload = {
        "phone_number": phone,
        "message": message,
        "message_type": "whatsapp",
        "api_key": TERMII_API_KEY,
    }

    try:
        response = requests.post(
            f"{TERMII_BASE_URL}/api/whatsapp/send",
            json=payload,
            timeout=10
        )
        return response.status_code, response.json()
    except Exception as e:
        return None, {"error": str(e)}



@csrf_exempt
def notify_defaulters(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST method required"}, status=400)

    # Parse JSON & remove duplicates
    try:
        data = json.loads(request.body)
        student_ids = list(set(data.get("student_ids", [])))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    if not student_ids:
        return JsonResponse({"error": "No students selected"}, status=400)

    students = Student.objects.filter(id__in=student_ids)
    if not students.exists():
        return JsonResponse({"error": "No students found"}, status=400)

    results = []
    used_phone_numbers = set()

    for student in students:
        phone_number = normalize_phone(student.phone_number)

        if not phone_number:
            results.append({
                "student": student.email,
                "status": "skipped",
                "reason": "No valid phone number"
            })
            continue

        # Prevent duplicate phone numbers
        if phone_number in used_phone_numbers:
            results.append({
                "student": student.email,
                "status": "skipped",
                "reason": "Phone number already notified"
            })
            continue

        used_phone_numbers.add(phone_number)
        print("📤 Sending messages to:", phone_number)

        next_due = (
            student.next_due_date.strftime("%d/%m/%Y")
            if student.next_due_date else "N/A"
        )

        message = (
            f"Dear {student.name or 'Student'}, your payment of N{student.amount_owed:,.0f} "
            f"is overdue. Kindly settle by {next_due}. Parach Academy."
        )

        # -----------------------
        # SEND SMS
        # -----------------------
        sms_payload = {
            "to": phone_number,
            "from": "ParachICT",
            "sms": message,
            "type": "plain",
            "channel": "generic",
            "api_key": TERMII_API_KEY
        }

        try:
            sms_response = requests.post(
                f"{TERMII_BASE_URL}/api/sms/send",
                json=sms_payload,
                timeout=10
            )
            sms_data = sms_response.json()
        except Exception as e:
            sms_data = {"error": str(e)}

        # -----------------------
        # SEND WHATSAPP
        # -----------------------
        wa_status, wa_data = send_whatsapp_message(phone_number, message)

        # -----------------------
        # FINAL RESULT
        # -----------------------
        results.append({
            "student": student.email,
            "phone": phone_number,
            "sms_response": sms_data,
            "whatsapp_response": wa_data
        })

        print("SMS Payload:", sms_payload)
        print("WhatsApp Payload:", {"phone_number": phone_number, "message": message})

    return JsonResponse({
        "message": f"Processed {len(results)} students (unique phones: {len(used_phone_numbers)})",
        "results": results
    })
















# # only sms fucntionality
# import json
# import requests
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.conf import settings
# from students.models import CustomUser as Student

# TERMII_API_KEY = settings.TERMII_API_KEY
# TERMII_BASE_URL = settings.TERMII_BASE_URL


# def normalize_phone(number):
#     """Convert phone number to international format (Nigeria example)."""
#     if not number:
#         return None
#     number = number.strip().replace(" ", "")
#     if number.startswith("0"):
#         number = "234" + number[1:]
#     elif number.startswith("+"):
#         number = number[1:]
#     return f"+{number}"


# @csrf_exempt
# def notify_defaulters(request):
#     if request.method != "POST":
#         return JsonResponse({"error": "POST method required"}, status=400)

#     # ---------------------------------------------
#     # 1️⃣ Parse JSON and remove duplicate IDs
#     # ---------------------------------------------
#     try:
#         data = json.loads(request.body)
#         student_ids = list(set(data.get("student_ids", [])))  # REMOVE DUPLICATE STUDENT IDs
#     except json.JSONDecodeError:
#         return JsonResponse({"error": "Invalid JSON"}, status=400)

#     if not student_ids:
#         return JsonResponse({"error": "No students selected"}, status=400)

#     students = Student.objects.filter(id__in=student_ids)

#     if not students.exists():
#         return JsonResponse({"error": "No students found"}, status=400)

#     results = []

#     # ---------------------------------------------
#     # 2️⃣ Prevent duplicate phone numbers from receiving SMS
#     # ---------------------------------------------
#     used_phone_numbers = set()

#     for student in students:
#         phone_number = normalize_phone(student.phone_number)

#         if not phone_number:
#             results.append({
#                 "student": student.email,
#                 "status": "skipped",
#                 "reason": "No valid phone number"
#             })
#             continue

#         # ---------------------------------------------
#         # 3️⃣ Unique phone protection
#         # Only send to each phone number ONCE
#         # ---------------------------------------------
#         if phone_number in used_phone_numbers:
#             results.append({
#                 "student": student.email,
#                 "status": "skipped",
#                 "reason": "Phone number already notified"
#             })
#             continue

#         used_phone_numbers.add(phone_number)

#         print("📤 Sending SMS to:", phone_number)

#         next_due = (
#             student.next_due_date.strftime("%d/%m/%Y")
#             if student.next_due_date else "N/A"
#         )

#         # ---------------------------------------------
#         # 4️⃣ SHORTENED MESSAGE - Keeps it under 160 characters
#         # Current length: ~145 characters (fits in 1 SMS)
#         # ---------------------------------------------
#         message = (
#             f"Dear {student.name or 'Student'}, your payment of N{student.amount_owed:,.0f} "
#             f"is overdue. Kindly settle by {next_due}. Parach Academy."
#         )

#         # Print message length for debugging
#         print(f"Message length: {len(message)} characters")
#         print(f"Message: {message}")

#         payload = {
#             "to": phone_number,
#             "from": "ParachICT",
#             "sms": message,
#             "type": "plain",
#             "channel": "generic",
#             "api_key": TERMII_API_KEY
#         }

#         try:
#             response = requests.post(
#                 f"{TERMII_BASE_URL}/api/sms/send",
#                 json=payload,
#                 timeout=10
#             )
#             resp_data = response.json()
#             print("Termii response:", resp_data)

#             if response.status_code == 200 and (
#                 resp_data.get("messageId") or resp_data.get("status") == "success"
#             ):
#                 results.append({
#                     "student": student.email,
#                     "status": "success",
#                     "phone": phone_number,
#                     "message_length": len(message),
#                     "termii_response": resp_data
#                 })
#             else:
#                 results.append({
#                     "student": student.email,
#                     "status": "failed",
#                     "phone": phone_number,
#                     "termii_response": resp_data
#                 })

#         except requests.RequestException as e:
#             results.append({
#                 "student": student.email,
#                 "status": "failed",
#                 "phone": phone_number,
#                 "error": str(e)
#             })
#             print(f"❌ Error sending SMS to {student.email}: {e}")

#     return JsonResponse({
#         "message": f"Processed {len(results)} students (unique phones: {len(used_phone_numbers)})",
#         "results": results
#     })