from operator import sub
import os
from django.shortcuts import render,redirect
from django.contrib import messages
from api.authentication.models import User
from django_tenants.utils import schema_context
from .forms import TenantSignupForm
from .tasks import create_tenant

# Create your views here.
from django.shortcuts import redirect, render
from rest_framework.decorators import api_view
from django.http import JsonResponse

def debug_request(request):
    return JsonResponse({
        "is_secure": request.is_secure(),
        "scheme": request.scheme,
        "http_x_forwarded_proto": request.META.get("HTTP_X_FORWARDED_PROTO"),
    })



@api_view(['GET'])
def get_auth_code(requests):
    pass

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
            messages.success(request, 'Tenant created successfully! Please check your email for the subscription link. and allow up to 10 minutes for the tenant to be fully set up. and then you can log in using your email and password that will be sent to you via email.')
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

