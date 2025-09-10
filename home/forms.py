from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

SUBSCRIPTION_CHOICES = [
    ('2000', '2,000 KES'),
    ('5000', '5,000 KES'),
    ('10000', '10,000 KES'),
    ('20000', '20,000 KES'),
    ('50000', '50,000 KES'),
]

class TenantSignupForm(forms.Form):
    full_name = forms.CharField(
        label="Full Name",
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'fullName', 'required': True, 'placeholder': 'John Doe'}),
    )
    email = forms.EmailField(
        label="Email address",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'id': 'emailAddress', 'required': True, 'placeholder': 'you@example.com'}),
    )
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'password1', 'required': True, 'placeholder': 'Enter your password'}),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'id': 'password2', 'required': True, 'placeholder': 'Confirm your password'}),
    )
    domain_name = forms.CharField(
        label="Tenant Domain Name",
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'domainName', 'required': True, 'placeholder': 'yourdomain'}),
        help_text="This will be your subdomain for the tenant."
    )
    subscription_plan = forms.ChoiceField(
        label="Select Subscription Plan (KES)",
        choices=SUBSCRIPTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'subscriptionPlan', 'required': True}),
    )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("The passwords do not match.")
        return password2

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if password1:
            validate_password(password1)
        return password1
