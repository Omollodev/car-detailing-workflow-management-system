"""
Forms for job management.
"""

from django import forms
from django.utils import timezone
from .models import Job, JobService
from apps.customers.models import Customer, Vehicle
from apps.services.models import Service
from apps.workers.models import WorkerProfile


class CustomerJobBookingForm(forms.Form):
    """
    Customer self-service: pick vehicle, services, and instructions (no internal fields).
    """

    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Vehicle',
    )
    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.filter(
            is_active=True,
            category=Service.Category.BASIC,
        ),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='Services needed',
    )
    priority = forms.ChoiceField(
        choices=Job.Priority.choices,
        initial=Job.Priority.NORMAL,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    special_instructions = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any special requests for this visit…',
        }),
    )

    def __init__(self, customer: Customer, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['vehicle'].queryset = Vehicle.objects.filter(
            customer=customer,
            is_active=True,
        )


class JobCreateForm(forms.ModelForm):
    """
    Form for creating a new job.
    """
    
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.filter(is_active=True),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'customer-select',
        }),
        help_text='Select customer or add new one'
    )
    
    vehicle = forms.ModelChoiceField(
        queryset=Vehicle.objects.none(),  # Will be populated via JavaScript
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'vehicle-select',
        }),
        help_text='Select vehicle'
    )
    
    assigned_worker = forms.ModelChoiceField(
        queryset=WorkerProfile.objects.none(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        help_text='Assign a worker (optional)'
    )
    
    services = forms.ModelMultipleChoiceField(
        queryset=Service.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input',
        }),
        help_text='Select services to perform'
    )
    
    class Meta:
        model = Job
        fields = ['customer', 'vehicle', 'assigned_worker', 'priority', 
                  'special_instructions', 'internal_notes']
        widgets = {
            'priority': forms.Select(attrs={
                'class': 'form-select',
            }),
            'special_instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Customer requests or special requirements',
            }),
            'internal_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Internal notes (staff only)',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate available workers
        self.fields['assigned_worker'].queryset = WorkerProfile.get_available_workers()
        
        # If customer is selected, populate vehicles
        if 'customer' in self.data:
            try:
                customer_id = int(self.data.get('customer'))
                self.fields['vehicle'].queryset = Vehicle.objects.filter(
                    customer_id=customer_id,
                    is_active=True
                )
            except (ValueError, TypeError):
                pass
        elif self.instance.pk:
            self.fields['vehicle'].queryset = Vehicle.objects.filter(
                customer=self.instance.customer,
                is_active=True
            )


class JobEditForm(forms.ModelForm):
    """
    Form for editing an existing job.
    """
    
    class Meta:
        model = Job
        fields = ['priority', 'special_instructions', 'internal_notes', 
                  'discount', 'payment_status', 'amount_paid']
        widgets = {
            'priority': forms.Select(attrs={
                'class': 'form-select',
            }),
            'special_instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
            }),
            'internal_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
            }),
            'discount': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
            }),
            'payment_status': forms.Select(attrs={
                'class': 'form-select',
            }),
            'amount_paid': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
            }),
        }


class JobStatusChangeForm(forms.Form):
    """
    Form for changing job status.
    """
    status = forms.ChoiceField(
        choices=Job.Status.choices,
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Add notes about this status change (optional)',
        })
    )


class JobAssignWorkerForm(forms.Form):
    """
    Form for assigning/reassigning a worker to a job.
    """
    worker = forms.ModelChoiceField(
        queryset=WorkerProfile.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='Assign Worker'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['worker'].queryset = WorkerProfile.get_available_workers()


class AddExtraServiceForm(forms.Form):
    """
    Form for adding an extra service to an existing job.
    """
    service = forms.ModelChoiceField(
        queryset=Service.objects.filter(is_active=True, category='extra'),
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='Extra Service'
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Notes about this service',
        })
    )
    price_override = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Override price (optional)',
            'step': '0.01',
        }),
        label='Custom Price (KES)'
    )


class JobServiceCompleteForm(forms.Form):
    """
    Form for marking a service as complete.
    """
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Completion notes (optional)',
        })
    )
    photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
        }),
        label='Photo evidence (optional)'
    )
