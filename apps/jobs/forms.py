"""
Forms for job management.
"""

from decimal import Decimal
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
            category__in=[
                Service.Category.EXTERIOR,
                Service.Category.INTERIOR,
            ],
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


class CashPaymentRecordingForm(forms.Form):
    """
    Manager records a cash payment for a job.
    """
    amount_paid = forms.DecimalField(
        min_value=Decimal('0.01'),
        max_digits=10,
        decimal_places=2,
        label='Amount received (KES)',
        widget=forms.NumberInput(
            attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
            }
        ),
    )
    payment_status = forms.ChoiceField(
        choices=[
            ('partial', 'Partial Payment'),
            ('paid', 'Fully Paid'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Payment Status',
        initial='paid',
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Notes about this cash payment (optional)',
            }
        ),
        label='Notes',
    )

    def __init__(self, *args, job=None, **kwargs):
        self.job = job
        super().__init__(*args, **kwargs)
        if job is not None:
            bal = job.balance_due
            self.fields['amount_paid'].help_text = (
                f'Balance due: KES {bal}. Enter the amount received.'
            )
            self.fields['amount_paid'].initial = bal

    def clean_amount_paid(self):
        amount = self.cleaned_data['amount_paid']
        if self.job is not None and amount > self.job.balance_due + Decimal('1'):
            # Allow small overpayment margin (1 KES) for rounding
            raise forms.ValidationError(
                f'Amount cannot exceed balance due (KES {self.job.balance_due}).'
            )
        return amount


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
        fields = [
            'priority',
            'special_instructions',
            'internal_notes',
            'discount',
            'payment_channel',
            'payment_status',
            'amount_paid',
        ]
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
            'payment_channel': forms.Select(attrs={
                'class': 'form-select',
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
        }),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Add notes about this status change (optional)',
        }),
    )

    def __init__(self, *args, job=None, **kwargs):
        super().__init__(*args, **kwargs)
        if job is not None and job.has_pending_services():
            self.fields['status'].choices = [
                c for c in Job.Status.choices if c[0] != Job.Status.COMPLETED
            ]


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
        queryset=Service.objects.filter(
            is_active=True,
            category__in=[
                Service.Category.DETAILING,
                Service.Category.ADDITIONAL,
            ],
        ),
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
