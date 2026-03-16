"""
Forms for customer and vehicle management.
"""

from django import forms
from .models import Customer, Vehicle


class CustomerForm(forms.ModelForm):
    """
    Form for creating and editing customers.
    """
    
    class Meta:
        model = Customer
        fields = ['name', 'phone', 'phone_secondary', 'email', 'address', 
                  'service_preferences', 'notes', 'is_vip']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Customer full name',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+254 7XX XXX XXX',
            }),
            'phone_secondary': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Alternative number (optional)',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@example.com',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Customer address',
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
        fields = ['plate_number', 'make', 'model', 'year', 'color', 
                  'vehicle_type', 'mileage', 'notes']
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
            'mileage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'Current mileage (km)',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Special notes about the vehicle',
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
