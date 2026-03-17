from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from apps.customers.models import Customer, Vehicle
from apps.jobs.models import Job, JobService
from apps.services.models import Service
from apps.workers.models import WorkerProfile

User = get_user_model()


class JobModelTests(TestCase):
    """Tests for core Job model behaviour."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="manager",
            password="testpass123",
            role="manager",
        )
        self.customer = Customer.objects.create(
            name="John Doe",
            phone="0712345678",
        )
        self.vehicle = Vehicle.objects.create(
            customer=self.customer,
            plate_number="KBX123A",
            make="Toyota",
            model="Corolla",
        )
        self.service_basic = Service.objects.create(
            name="Full Wash",
            price=Decimal("500.00"),
            estimated_duration=30,
            category="basic",
        )
        self.service_extra = Service.objects.create(
            name="Engine Wash",
            price=Decimal("800.00"),
            estimated_duration=40,
            category="extra",
        )
        self.worker_user = User.objects.create_user(
            username="worker",
            password="testpass123",
            role="worker",
        )
        self.worker = WorkerProfile.objects.create(user=self.worker_user)

        self.job = Job.objects.create(
            customer=self.customer,
            vehicle=self.vehicle,
            created_by=self.user,
            assigned_worker=self.worker,
        )
        JobService.objects.create(job=self.job, service=self.service_basic)
        JobService.objects.create(job=self.job, service=self.service_extra)

    def test_calculate_totals(self):
        """Job.calculate_totals should sum prices and durations."""
        self.job.calculate_totals()
        self.job.refresh_from_db()
        self.assertEqual(self.job.estimated_price, Decimal("1300.00"))
        self.assertEqual(self.job.estimated_duration, 70)

    def test_has_pending_extra_services_true(self):
        """Job.has_pending_extra_services should detect incomplete extras."""
        self.assertTrue(self.job.has_pending_extra_services())

    def test_change_status_blocks_completion_with_pending_extras(self):
        """Jobs cannot be completed while extra services are pending."""
        can_change = self.job.change_status("completed", user=self.user)
        self.assertFalse(can_change)
        self.assertNotEqual(self.job.status, "completed")

    def test_change_status_valid_transition(self):
        """Valid status transitions should succeed and update status."""
        self.assertTrue(self.job.change_status("in_progress", user=self.user))
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, "in_progress")


class JobViewsTests(TestCase):
    """Smoke tests for key job views."""

    def setUp(self):
        self.client = Client()
        self.manager = User.objects.create_user(
            username="manager",
            password="testpass123",
            role="manager",
        )
        self.customer = Customer.objects.create(
            name="Jane Doe",
            phone="0711111111",
        )
        self.vehicle = Vehicle.objects.create(
            customer=self.customer,
            plate_number="KBZ999Z",
            make="Nissan",
            model="Note",
        )
        self.service = Service.objects.create(
            name="Quick Wash",
            price=Decimal("300.00"),
            estimated_duration=20,
            category="basic",
        )
        self.client.login(username="manager", password="testpass123")

    def test_job_list_view_ok(self):
        url = reverse("jobs:list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_job_create_view_get_ok(self):
        url = reverse("jobs:create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class JobApiTests(TestCase):
    """Tests for dashboard/job AJAX APIs."""

    def setUp(self):
        self.client = Client()
        self.manager = User.objects.create_user(
            username="manager",
            password="testpass123",
            role="manager",
        )
        self.customer = Customer.objects.create(
            name="API Customer",
            phone="0700000000",
        )
        self.vehicle = Vehicle.objects.create(
            customer=self.customer,
            plate_number="KCA000A",
            make="Honda",
            model="Fit",
        )
        self.job = Job.objects.create(
            customer=self.customer,
            vehicle=self.vehicle,
            created_by=self.manager,
        )
        self.client.login(username="manager", password="testpass123")

    def test_dashboard_stats_api_requires_auth(self):
        self.client.logout()
        response = self.client.get("/api/dashboard/stats/")
        self.assertEqual(response.status_code, 401)

    def test_dashboard_stats_api_ok(self):
        response = self.client.get("/api/dashboard/stats/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("waiting", data)
        self.assertIn("revenue_today", data)

