#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path

def create_initial_data():
    """Create initial data for the application."""
    from django.contrib.auth import get_user_model
    from apps.services.models import ServiceCategory, Service
    
    User = get_user_model()
    
    # Create admin user if doesn't exist
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@safi.com',
            password='passs@123',
            first_name='Admin',
            last_name='User',
            role='admin'
        )
        print("Created admin user (username: admin, password: passs@123)")
    
    # Create service categories and services
    categories_data = {
        'Exterior': [
            ('Basic Wash', 300, 20, 'Quick exterior wash with hand dry'),
            ('Full Wash', 500, 30, 'Complete exterior wash, windows, and hand dry'),
            ('Foam Wash', 700, 45, 'Premium foam wash with wax protection'),
            ('Engine Wash', 500, 30, 'Engine bay cleaning and degreasing'),
        ],
        'Interior': [
            ('Interior Vacuum', 300, 20, 'Full interior vacuum cleaning'),
            ('Interior Deep Clean', 800, 60, 'Deep interior cleaning with shampoo'),
            ('Leather Treatment', 600, 45, 'Leather conditioning and protection'),
            ('Dashboard Polish', 200, 15, 'Dashboard and trim polishing'),
        ],
        'Detailing': [
            ('Full Detail', 3000, 180, 'Complete interior and exterior detailing'),
            ('Paint Correction', 5000, 300, 'Paint correction and polishing'),
            ('Ceramic Coating', 15000, 480, 'Premium ceramic coating protection'),
            ('Headlight Restoration', 1500, 60, 'Headlight lens restoration'),
        ],
        'Additional Services': [
            ('Air Freshener', 200, 5, 'Premium car air freshener'),
            ('Tire Dressing', 300, 15, 'Tire shine and dressing'),
            ('Windshield Treatment', 500, 20, 'Water-repellent windshield treatment'),
        ]
    }
    
    for category_name, services in categories_data.items():
        category, created = ServiceCategory.objects.get_or_create(name=category_name)
        if created:
            print(f"Created category: {category_name}")
        
        for service_name, price, duration, description in services:
            service, created = Service.objects.get_or_create(
                name=service_name,
                defaults={
                    'category': category,
                    'price': price,
                    'estimated_duration': duration,
                    'description': description
                }
            )
            if created:
                print(f"  Created service: {service_name}")
    
    print("\nInitial data setup complete!")
    print("\n--- Login Credentials ---")
    print("Username: admin")
    print("Password: passs@123")
    print("-------------------------")


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    # Check for setup command
    if len(sys.argv) > 1 and sys.argv[1] == 'setup':
        import django
        django.setup()
        create_initial_data()
        return
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
