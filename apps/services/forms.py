"""
Forms for service management.
"""

from django import forms
from .models import Service


class ServiceForm(forms.ModelForm):
    """
    Form for creating and editing services.
    """
    
    class Meta:
        model = Service
        fields = ['name', 'description', 'category', 'price', 'estimated_duration', 
                  'is_active', 'requires_special_equipment', 'display_order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Service name',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe the service...',
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01',
                'placeholder': '0.00',
            }),
            'estimated_duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': 'Duration in minutes',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'requires_special_equipment': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'display_order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
            }),
        }
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price < 0:
            raise forms.ValidationError('Price cannot be negative.')
        return price
    
    def clean_estimated_duration(self):
        duration = self.cleaned_data.get('estimated_duration')
        if duration and duration < 1:
            raise forms.ValidationError('Duration must be at least 1 minute.')
        return duration
