# Generated manually for customer portal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('customers', '0002_alter_vehicle_vehicle_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='business_name',
            field=models.CharField(
                blank=True,
                help_text='Optional business or fleet name for this account',
                max_length=200,
                verbose_name='Business / store name',
            ),
        ),
        migrations.AddField(
            model_name='customer',
            name='user',
            field=models.OneToOneField(
                blank=True,
                help_text='Linked login for customer self-service (optional for walk-in records)',
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='customer_profile',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Portal account',
            ),
        ),
    ]
