import os
from django.shortcuts import render,redirect
from api.helpers.models import Client, Domain
from api.authentication.models import User
from django_tenants.utils import schema_context
from django.utils import timezone
from .forms import TenantSignupForm
from .tasks import create_tenant

# Create your views here.
@schema_context('public')
def home(request):
    form = TenantSignupForm()
    if request.method == 'POST':
        form = TenantSignupForm(request.POST)
        if form.is_valid():
            # Create the user
            User.objects.create_user(
                username=form.cleaned_data['email'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1']
            )
            # import pdb; pdb.set_trace()
            # create_tenant.delay(form.cleaned_data['domain_name'])
            create_tenant.delay(domain_name=form.cleaned_data['domain_name'], email=form.cleaned_data['email'])
            # Redirect or show a success message as needed
            redirect('home')  # Redirect to the home page or any other page
    return render(request, 'home/index.html', {'form': form})  # Render the home.html template
