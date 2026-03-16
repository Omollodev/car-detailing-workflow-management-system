from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.jobs.models import Job, JobStatusLog
from apps.customers.models import Customer, Vehicle
from apps.services.models import Service, ServiceCategory
from apps.workers.models import Worker

User = get_user_model()


class JobModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.customer = Customer.objects.create(
            name='John Doe',
            phone='0712345678',
            created_by=self.user
        )
        self.vehicle = Vehicle.objects.create(
            customer=self.customer,
            make='Toyota',
            model='Corolla',
            registration_number='KBX 123A'
        )
        self.category = ServiceCategory.objects.create(name='Exterior')
        self.service = Service.objects.create(
            name='Full Wash',
            price=Decimal('500.00'),
            estimated_duration=30,
            category=self.category
        )
        self.job = Job.objects.create(
            customer=self.customer,
            vehicle=self.vehicle,
            created_by=self.user
        )
        self.job.services.add(self.service)

    def test_job_creation(self):
        """Test job is created correctly"""
        self.assertEqual(self.job.customer, self.customer)
        self.assertEqual(self.job.vehicle, self.vehicle)
        self.assertEqual(self.job.status, 'pending')

    def test_job_number_generation(self):
        """Test job number is auto-generated"""
        self.assertTrue(self.job.job_number.startswith('JOB-'))

    def test_job_total_price(self):
        """Test job total price calculation"""
        self.assertEqual(self.job.total_price, Decimal('500.00'))

    def test_job_final_price_with_discount(self):
        """Test final price with discount"""
        self.job.discount = Decimal('100.00')
        self.job.save()
        self.assertEqual(self.job.final_price, Decimal('400.00'))

    def test_job_status_transition(self):
        """Test job status transitions"""
        self.job.start_job(self.user)
        self.assertEqual(self.job.status, 'in_progress')
        
        self.job.complete_job(self.user)
        self.assertEqual(self.job.status, 'completed')

    def test_job_cannot_complete_from_pending(self):
        """Test job cannot be completed directly from pending"""
        # This should raise an exception or not change status
        with self.assertRaises(Exception):
            self.job.complete_job(self.user)


class JobStatusLogTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.customer = Customer.objects.create(
            name='John Doe',
            phone='0712345678',
            created_by=self.user
        )
        self.vehicle = Vehicle.objects.create(
            customer=self.customer,
            make='Toyota',
            model='Corolla',
            registration_number='KBX 123A'
        )
        self.job = Job.objects.create(
            customer=self.customer,
            vehicle=self.vehicle,
            created_by=self.user
        )

    def test_status_log_creation(self):
        """Test status log is created on status change"""
        initial_count = JobStatusLog.objects.filter(job=self.job).count()
        self.job.start_job(self.user)
        new_count = JobStatusLog.objects.filter(job=self.job).count()
        self.assertEqual(new_count, initial_count + 1)

    def test_status_log_records_user(self):
        """Test status log records the user who made the change"""
        self.job.start_job(self.user)
        log = JobStatusLog.objects.filter(job=self.job).last()
        self.assertEqual(log.changed_by, self.user)


class JobViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='manager'
        )
        self.customer = Customer.objects.create(
            name='John Doe',
            phone='0712345678',
            created_by=self.user
        )
        self.vehicle = Vehicle.objects.create(
            customer=self.customer,
            make='Toyota',
            model='Corolla',
            registration_number='KBX 123A'
        )
        self.category = ServiceCategory.objects.create(name='Exterior')
        self.service = Service.objects.create(
            name='Full Wash',
            price=Decimal('500.00'),
            estimated_duration=30,
            category=self.category
        )
        self.job = Job.objects.create(
            customer=self.customer,
            vehicle=self.vehicle,
            created_by=self.user
        )
        self.job.services.add(self.service)
        self.client.login(username='testuser', password='testpass123')

    def test_job_list_view(self):
        """Test job list view"""
        response = self.client.get(reverse('jobs:job_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.job.job_number)

    def test_job_detail_view(self):
        """Test job detail view"""
        response = self.client.get(reverse('jobs:job_detail', args=[self.job.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.customer.name)

    def test_job_create_view(self):
        """Test job creation view"""
        response = self.client.get(reverse('jobs:job_create'))
        self.assertEqual(response.status_code, 200)

    def test_job_create_post(self):
        """Test job creation via POST"""
        response = self.client.post(reverse('jobs:job_create'), {
            'customer': self.customer.pk,
            'vehicle': self.vehicle.pk,
            'services': [self.service.pk],
            'priority': 'normal'
        })
        self.assertEqual(response.status_code, 302)  # Redirect on success
        self.assertEqual(Job.objects.count(), 2)

    def test_job_start_action(self):
        """Test starting a job"""
        response = self.client.post(reverse('jobs:job_start', args=[self.job.pk]))
        self.assertEqual(response.status_code, 302)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, 'in_progress')


class JobAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='manager'
        )
        self.customer = Customer.objects.create(
            name='John Doe',
            phone='0712345678',
            created_by=self.user
        )
        self.vehicle = Vehicle.objects.create(
            customer=self.customer,
            make='Toyota',
            model='Corolla',
            registration_number='KBX 123A'
        )
        self.job = Job.objects.create(
            customer=self.customer,
            vehicle=self.vehicle,
            created_by=self.user
        )
        self.client.login(username='testuser', password='testpass123')

    def test_api_update_status(self):
        """Test API endpoint for updating job status"""
        response = self.client.post(
            reverse('jobs:api_update_status', args=[self.job.pk]),
            {'status': 'in_progress'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, 'in_progress')

    def test_api_kanban_data(self):
        """Test API endpoint for kanban board data"""
        response = self.client.get(reverse('jobs:api_kanban'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('pending', data)
        self.assertIn('in_progress', data)
        self.assertIn('completed', data)
