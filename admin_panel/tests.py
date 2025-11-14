from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import AdminActivity, Notification
from students.models import CustomUser

User = get_user_model()


class AdminPanelTestCase(TestCase):
    def setUp(self):
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='admin123'
        )
        
        # Create regular user
        self.student_user = CustomUser.objects.create_user(
            username='student',
            email='student@test.com',
            password='student123',
            is_staff=False
        )
        
        self.client = APIClient()
    
    def test_dashboard_stats_authenticated(self):
        """Test dashboard stats endpoint with authentication"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/admin-panel/dashboard/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_students', response.data)
    
    def test_dashboard_stats_unauthenticated(self):
        """Test dashboard stats endpoint without authentication"""
        response = self.client.get('/api/admin-panel/dashboard/stats/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_notification(self):
        """Test notification creation"""
        notification = Notification.objects.create(
            title="Test Notification",
            message="This is a test",
            priority="HIGH"
        )
        self.assertEqual(notification.title, "Test Notification")
        self.assertFalse(notification.is_read)
    
    def test_admin_activity_logging(self):
        """Test admin activity logging"""
        activity = AdminActivity.objects.create(
            admin=self.admin_user,
            action='CREATE',
            model_name='Student',
            description="Created new student"
        )
        self.assertEqual(activity.action, 'CREATE')
        self.assertEqual(activity.admin, self.admin_user)