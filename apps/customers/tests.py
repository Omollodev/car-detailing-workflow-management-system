from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.customers.models import Customer, Vehicle

User = get_user_model()


class CustomerModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.customer = Customer.objects.create(
            name='John Doe',
            phone='0712345678',
            email='john@example.com',
            created_by=self.user
        )

    def test_customer_creation(self):
        """Test customer is created correctly"""
        self.assertEqual(self.customer.name, 'John Doe')
        self.assertEqual(self.customer.phone, '0712345678')
        self.assertEqual(self.customer.email, 'john@example.com')

    def test_customer_str(self):
        """Test customer string representation"""
        self.assertEqual(str(self.customer), 'John Doe - 0712345678')

    def test_customer_phone_validation(self):
        """Test phone number format is validated"""
        # This depends on your validation implementation
        customer = Customer.objects.create(
            name='Jane Doe',
            phone='0700000000',
            created_by=self.user
        )
        self.assertTrue(customer.phone.startswith('07') or customer.phone.startswith('+254'))


class VehicleModelTests(TestCase):
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
            year=2020,
            registration_number='KBX 123A',
            color='White'
        )

    def test_vehicle_creation(self):
        """Test vehicle is created correctly"""
        self.assertEqual(self.vehicle.make, 'Toyota')
        self.assertEqual(self.vehicle.model, 'Corolla')
        self.assertEqual(self.vehicle.registration_number, 'KBX 123A')

    def test_vehicle_str(self):
        """Test vehicle string representation"""
        expected = '2020 Toyota Corolla (KBX 123A)'
        self.assertEqual(str(self.vehicle), expected)

    def test_vehicle_belongs_to_customer(self):
        """Test vehicle is associated with customer"""
        self.assertEqual(self.vehicle.customer, self.customer)
        self.assertIn(self.vehicle, self.customer.vehicles.all())

    def test_unique_registration_number(self):
        """Test registration number must be unique"""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Vehicle.objects.create(
                customer=self.customer,
                make='Honda',
                model='Civic',
                registration_number='KBX 123A'  # Same as existing
            )


class CustomerViewTests(TestCase):
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
        self.client.login(username='testuser', password='testpass123')

    def test_customer_list_view(self):
        """Test customer list view"""
        response = self.client.get(reverse('customers:customer_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')

    def test_customer_detail_view(self):
        """Test customer detail view"""
        response = self.client.get(reverse('customers:customer_detail', args=[self.customer.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.customer.name)
        self.assertContains(response, self.customer.phone)

    def test_customer_create_view(self):
        """Test customer creation"""
        response = self.client.post(reverse('customers:customer_create'), {
            'name': 'Jane Smith',
            'phone': '0798765432',
            'email': 'jane@example.com'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Customer.objects.filter(name='Jane Smith').exists())

    def test_customer_search(self):
        """Test customer search functionality"""
        response = self.client.get(reverse('customers:customer_list'), {'q': 'John'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')

    def test_vehicle_create_view(self):
        """Test vehicle creation for customer"""
        response = self.client.post(
            reverse('customers:vehicle_create', args=[self.customer.pk]),
            {
                'make': 'Honda',
                'model': 'Civic',
                'registration_number': 'KCD 456B',
                'year': 2021
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Vehicle.objects.filter(registration_number='KCD 456B').exists())


class CustomerAPITests(TestCase):
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
        self.client.login(username='testuser', password='testpass123')

    def test_api_get_customer_vehicles(self):
        """Test API endpoint to get customer vehicles"""
        response = self.client.get(f'/api/customers/{self.customer.pk}/vehicles/')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['vehicles']), 1)
        self.assertEqual(data['vehicles'][0]['registration'], 'KBX 123A')
