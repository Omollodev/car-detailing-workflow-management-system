"""
Forms for user authentication and management.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class LoginForm(AuthenticationForm):
    """
    Custom login form with Bootstrap styling.
    """
    username = forms.CharField(
        label=_('Username'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        label=_('Remember me'),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
        })
    )


class CustomerRegistrationForm(UserCreationForm):
    """
    Public self-registration: creates a User with role=customer and linked Customer profile.
    Workers and staff are created only by admin/manager.
    """

    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'First name',
    }))
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Last name',
    }))
    email = forms.EmailField(
        required=True,
        help_text='Use a Gmail address (@gmail.com).',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'you@gmail.com',
            'autocomplete': 'email',
        }),
    )
    phone = forms.CharField(max_length=20, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': '+254 7XX XXX XXX',
    }))

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Choose a username',
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm password',
        })

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            raise ValidationError('Email is required.')
        allowed = ('@gmail.com', '@googlemail.com','@yahoo.com','@outlook.com','@hotmail.com')
        if not any(email.endswith(s) for s in allowed):
            raise ValidationError(
                'Please register with a Gmail address (e.g. you@gmail.com, you@yahoo.com, you@outlook.com, you@hotmail.com).'
            )
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data['phone']
        user.role = User.Role.CUSTOMER
        user.is_active = True
        if commit:
            user.save()
        return user


class UserRegistrationForm(UserCreationForm):
    """
    Form for registering new users (admin only).
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com',
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'role', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+254 7XX XXX XXX',
            }),
            'role': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password',
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password',
        })
        # Staff accounts only — customers use the public registration flow
        if 'role' in self.fields:
            staff_roles = [
                c for c in User.Role.choices if c[0] != User.Role.CUSTOMER
            ]
            self.fields['role'].choices = staff_roles


class UserUpdateForm(forms.ModelForm):
    """
    Form for updating user profile.
    """
    
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'address',
            'profile_pic',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Optional',
            }),
            'profile_pic': forms.FileInput(attrs={
                'class': 'form-control',
            }),
        }


class UserAdminForm(forms.ModelForm):
    """
    Form for admin to edit user details including role.
    """
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 
                  'role', 'is_active', 'is_active_worker']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
            }),
            'role': forms.Select(attrs={
                'class': 'form-select',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'is_active_worker': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
