from django import forms
from .models import FreelancerProfile

class FreelancerProfileForm(forms.ModelForm):
    class Meta:
        model = FreelancerProfile
        fields = ['bio', 'resume', 'hourly_rate']
