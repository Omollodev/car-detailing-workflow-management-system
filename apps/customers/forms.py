"""
Forms for customer and vehicle management.
"""

from decimal import Decimal

from django import forms
from apps.jobs.models import Job
from .models import Customer, Vehicle


class PaymentMethodSelectionForm(forms.Form):
    """
    Customer selects payment method: M-Pesa or Cash.
    """
    payment_method = forms.ChoiceField(
        choices=[
            ('mpesa', 'M-Pesa (Automatic Payment)'),
            ('cash', 'Cash at the shop (Manager will record)'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='How would you like to pay?',
        help_text='Choose your preferred payment method. Once saved, the manager can change this if needed.'
    )


class CustomerMpesaPaymentForm(forms.Form):
    """
    Customer records an M-Pesa payment; amounts apply immediately (reconcile with Daraja later).
    """

    amount = forms.DecimalField(
        min_value=Decimal('0.01'),
        max_digits=10,
        decimal_places=2,
        label='Amount sent (KES)',
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
            }
        ),
    )
    mpesa_phone = forms.CharField(
        max_length=20,
        label='M-Pesa phone number',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': '07XX XXX XXX',
            }
        ),
    )
    mpesa_transaction_id = forms.CharField(
        max_length=64,
        label='M-Pesa confirmation code',
        help_text='The code from your MPESA SMS (e.g. QK1ABC2345).',
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Transaction ID',
            }
        ),
    )

    def __init__(self, *args, job=None, **kwargs):
        self.job = job
        super().__init__(*args, **kwargs)
        if job is not None:
            bal = job.balance_due
            self.fields['amount'].help_text = (
                f'Balance due: KES {bal}. You can pay in full or part of this amount.'
            )

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        job = self.job
        if job is not None and amount > job.balance_due:
            raise forms.ValidationError(
                f'Amount cannot exceed balance due (KES {job.balance_due}).'
            )
        return amount


class CustomerForm(forms.ModelForm):
    """
    Form for creating and editing customers.
    """
    
    class Meta:
        model = Customer
        fields = [
            'name',
            'phone',
            'email',
            'service_preferences',
            'notes',
            'is_vip',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Customer full name',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+254 7XX XXX XXX',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com',
            }),
            'service_preferences': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Any special preferences or requirements',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Additional notes',
            }),
            'is_vip': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Basic phone validation
            phone = phone.replace(' ', '').replace('-', '')
            if not phone.replace('+', '').isdigit():
                raise forms.ValidationError('Please enter a valid phone number.')
        return phone


class VehicleForm(forms.ModelForm):
    """
    Form for creating and editing vehicles.
    """
    
    class Meta:
        model = Vehicle
        fields = [
            'plate_number',
            'make',
            'model',
            'year',
            'color',
            'vehicle_type',
        ]
        widgets = {
            'plate_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'KXX 123X',
                'style': 'text-transform: uppercase;',
            }),
            'make': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Toyota, Honda',
            }),
            'model': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Corolla, Civic',
            }),
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1970',
                'max': '2030',
                'placeholder': 'YYYY',
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Vehicle color',
            }),
            'vehicle_type': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
    
    def clean_plate_number(self):
        plate = self.cleaned_data.get('plate_number')
        if plate:
            plate = plate.upper().strip()
            # Check for uniqueness, excluding current instance
            qs = Vehicle.objects.filter(plate_number__iexact=plate)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError('A vehicle with this plate number already exists.')
        return plate


class QuickCustomerVehicleForm(forms.Form):
    """
    Quick form for creating a new customer with a vehicle in one step.
    """
    # Customer fields
    customer_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Customer name',
        })
    )
    customer_phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+254 7XX XXX XXX',
        })
    )
    
    # Vehicle fields
    plate_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'KXX 123X',
            'style': 'text-transform: uppercase;',
        })
    )
    make = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Toyota',
        })
    )
    model = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Corolla',
        })
    )
    vehicle_type = forms.ChoiceField(
        choices=Vehicle.VehicleType.choices,
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    
    def clean_plate_number(self):
        plate = self.cleaned_data.get('plate_number')
        if plate:
            plate = plate.upper().strip()
            if Vehicle.objects.filter(plate_number__iexact=plate).exists():
                raise forms.ValidationError('A vehicle with this plate number already exists.')
        return plate
    
    def save(self):
        """Create customer and vehicle from form data."""
        customer = Customer.objects.create(
            name=self.cleaned_data['customer_name'],
            phone=self.cleaned_data['customer_phone'],
        )
        
        vehicle = Vehicle.objects.create(
            customer=customer,
            plate_number=self.cleaned_data['plate_number'],
            make=self.cleaned_data['make'],
            model=self.cleaned_data['model'],
            vehicle_type=self.cleaned_data['vehicle_type'],
        )
        
        return customer, vehicle


class CustomerPortalProfileForm(forms.ModelForm):
    """
    Form for customers to update contact details (streamlined portal).
    """

    class Meta:
        model = Customer
        fields = [
            'name',
            'phone',
            'phone_secondary',
            'email',
            'service_preferences',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_secondary': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'you@gmail.com',
            }),
            'service_preferences': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Preferred services or short notes for the shop',
            }),
        }

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            return email
        allowed = ('@gmail.com', '@googlemail.com','@yahoo.com','@outlook.com','@hotmail.com')
        if not any(email.endswith(s) for s in allowed):
            raise forms.ValidationError(
                'Please use a Gmail address (e.g. you@gmail.com, you@yahoo.com, you@outlook.com, you@hotmail.com).'
            )
        return email
