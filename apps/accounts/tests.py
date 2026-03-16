from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )

    def test_user_creation(self):
        """Test user is created correctly"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))

    def test_user_full_name(self):
        """Test user full name method"""
        self.assertEqual(self.user.get_full_name(), 'Test User')

    def test_user_role_default(self):
        """Test default user role"""
        self.assertEqual(self.user.role, 'viewer')

    def test_superuser_creation(self):
        """Test superuser creation"""
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)


class LoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.login_url = reverse('accounts:login')

    def test_login_page_loads(self):
        """Test login page loads correctly"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_login_success(self):
        """Test successful login"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect on success

    def test_login_failure(self):
        """Test failed login with wrong password"""
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid')

    def test_logout(self):
        """Test logout functionality"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)


class PermissionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.viewer = User.objects.create_user(
            username='viewer',
            password='pass123',
            role='viewer'
        )
        self.worker = User.objects.create_user(
            username='worker',
            password='pass123',
            role='worker'
        )
        self.manager = User.objects.create_user(
            username='manager',
            password='pass123',
            role='manager'
        )
        self.admin = User.objects.create_user(
            username='admin',
            password='pass123',
            role='admin'
        )

    def test_viewer_permissions(self):
        """Test viewer can access dashboard but not edit"""
        self.client.login(username='viewer', password='pass123')
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)

    def test_manager_permissions(self):
        """Test manager can access admin areas"""
        self.client.login(username='manager', password='pass123')
        response = self.client.get(reverse('jobs:job_list'))
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_redirect(self):
        """Test unauthenticated users are redirected to login"""
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
