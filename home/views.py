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
from blog.models import BlogPost

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
    posts = BlogPost.objects.order_by('-created_at')[:3]  # latest 3 posts
    if request.method == 'POST':
        form = TenantSignupForm(request.POST)
        if form.is_valid():
            User.objects.create_user(
                username=form.cleaned_data['instagram_username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password1']
            )
            create_tenant.delay(
                domain_name=form.cleaned_data['domain_name'], 
                email=form.cleaned_data['email'], 
                subscription=form.cleaned_data['subscription_plan'],
                phone_number=form.cleaned_data['phone_number'],
                whatsapp_channel_id=form.cleaned_data['whatsapp_channel_id'],
                whatsapp_channel_token=form.cleaned_data['whatsapp_channel_token']
            )
            messages.success(
                request,
                "🎉 Tenant created successfully! Please check your email for your subscription link. "
                "Setup may take up to 10 minutes. Once completed, you can log in with the same email and password you registered with."
            )

            return redirect('home')

    host = request.get_host().split(':')[0]  # hostname without port
    main_domain = 'lunyamwi.org'
    local_main = 'localhost'
    
    if host == main_domain or host == local_main:
        # Plain main domain or localhost - render home
        return render(request, 'home/index.html', {'form': form, 'posts': posts})
    elif host.endswith('.' + main_domain) or host.endswith('.' + local_main):
        # Subdomain on production domain or local subdomain - redirect
        return redirect('accounts/login')  # replace with your subdomain view
    else:
        # fallback
        return render(request, 'home/index.html', {'form': form, 'posts': posts})



def privacy_gmail(request):
    return render(request, 'home/privacy_gmail.html')