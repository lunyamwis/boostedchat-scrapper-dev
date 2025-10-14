import re
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

SUBSCRIPTION_CHOICES = [
    ('0', 'Free'),
    ('7000', '7,000 KES'),
    ('10000', '10,000 KES'),
    ('15000', '15,000 KES'),
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
        label="Domain Name (Company Name)",
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'domainName', 'required': True, 'placeholder': 'yourdomain'}),
        help_text="This will be your subdomain."
    )
    
    subscription_plan = forms.ChoiceField(
        label="Select Subscription Plan (KES)",
        choices=SUBSCRIPTION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'subscriptionPlan', 'required': True}),
    )
    phone_number = forms.RegexField(
        label="Phone Number",
        regex=r'^\+?[1-9]\d{7,14}$',  # E.164 format
        max_length=15,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'id': 'phoneNumber',
                'required': True,
                'placeholder': '+254712345678'
            }
        ),
        help_text="Enter phone number in international format, e.g. +254712345678. Your WhatsApp number must be a Whatsapp business number."
    )

    whatsapp_channel_id = forms.CharField(
        label="WhatsApp Channel ID",
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'whatsappChannelId', 'required': False, 'placeholder': 'Your WhatsApp Channel ID'}),
        help_text="This is the ID of your WhatsApp Business API channel."
    )
    whatsapp_channel_token = forms.CharField(
        label="WhatsApp Channel Token",
        max_length=2048,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'whatsappChannelToken', 'required': False, 'placeholder': 'Your WhatsApp Channel Token'}),
        help_text="This is the token of your WhatsApp Business API channel."
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

    def clean_domain_name(self):
        domain = self.cleaned_data.get('domain_name')

        # Convert to lowercase
        domain = domain.lower()

        # Remove spaces
        domain = domain.replace(' ', '')

        # Validate domain format for subdomain:
        # - Only letters, digits, and hyphens allowed
        # - Cannot start or end with a hyphen
        # - Length rules generally apply (1-63 characters)
        if not re.match(r'^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?$', domain):
            raise ValidationError(
                "Invalid domain name: only lowercase letters, numbers, and hyphens are allowed. "
                "Cannot start or end with a hyphen."
            )
        return domain