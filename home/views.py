from operator import sub
import os
from django.shortcuts import render,redirect
from api.helpers.models import Client, Domain
from api.authentication.models import User
from django_tenants.utils import schema_context
from django.utils import timezone
from .forms import TenantSignupForm
from .tasks import create_tenant

# Create your views here.
from django.shortcuts import redirect, render

@schema_context('public')
def home(request):
    form = TenantSignupForm()
    if request.method == 'POST':
        form = TenantSignupForm(request.POST)
        if form.is_valid():
            User.objects.create_user(
                username=form.cleaned_data['email'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1']
            )
            create_tenant.delay(
                domain_name=form.cleaned_data['domain_name'], 
                email=form.cleaned_data['email'], 
                subscription=form.cleaned_data['subscription_plan']
            )
            return redirect('home')

    host = request.get_host().split(':')[0]  # hostname without port
    main_domain = 'lunyamwi.org'
    local_main = 'localhost'
    
    if host == main_domain or host == local_main:
        # Plain main domain or localhost - render home
        return render(request, 'home/index.html', {'form': form})
    elif host.endswith('.' + main_domain) or host.endswith('.' + local_main):
        # Subdomain on production domain or local subdomain - redirect
        return redirect('accounts/login')  # replace with your subdomain view
    else:
        # fallback
        return render(request, 'home/index.html', {'form': form})

