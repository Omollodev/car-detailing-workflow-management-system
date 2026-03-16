"""
Forms for worker management.
"""

from django import forms
from .models import WorkerProfile
from apps.services.models import Service


class WorkerProfileForm(forms.ModelForm):
    """
    Form for editing worker profile details.
    """
    
    class Meta:
        model = WorkerProfile
        fields = ['skills', 'is_available', 'employee_id', 'hired_date', 'notes']
        widgets = {
            'skills': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input',
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'employee_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Employee ID',
            }),
            'hired_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['skills'].queryset = Service.objects.filter(is_active=True)


class WorkerAssignmentForm(forms.Form):
    """
    Form for assigning a worker to a job.
    """
    worker = forms.ModelChoiceField(
        queryset=WorkerProfile.objects.filter(is_available=True),
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='Assign Worker'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['worker'].queryset = WorkerProfile.get_available_workers()


class WorkerAvailabilityForm(forms.Form):
    """
    Form for toggling worker availability.
    """
    is_available = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        }),
        label='Available for assignments'
    )
