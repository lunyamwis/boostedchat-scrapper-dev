from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import FreelancerProfile, Payment
from .forms import FreelancerProfileForm
from django.conf import settings
import requests

# Freelancer dashboard
@login_required
def profile_create(request):
    try:
        profile = request.user.freelancerprofile
        form = FreelancerProfileForm(instance=profile)
    except FreelancerProfile.DoesNotExist:
        form = FreelancerProfileForm()
    
    if request.method == "POST":
        form = FreelancerProfileForm(request.POST, request.FILES, instance=getattr(request.user, 'freelancerprofile', None))
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            return redirect('profile_detail', profile.id)

    return render(request, 'marketplace/profile_form.html', {'form': form})

@login_required
def profile_detail(request, pk):
    profile = get_object_or_404(FreelancerProfile, pk=pk)
    return render(request, 'marketplace/profile_detail.html', {'freelancer': profile})

# Browse freelancers
def freelancer_list(request):
    freelancers = FreelancerProfile.objects.all()
    return render(request, 'marketplace/freelancer_list.html', {'freelancers': freelancers})

# Paystack payment
@login_required
def paystack_payment(request, freelancer_id):
    freelancer = get_object_or_404(FreelancerProfile, id=freelancer_id)
    amount = int(freelancer.hourly_rate * 100)  # Paystack uses kobo
    callback_url = request.build_absolute_uri(f'/payment/callback/{freelancer.id}/')

    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    data = {
        "email": request.user.email,
        "amount": amount,
        "callback_url": callback_url
    }
    response = requests.post("https://api.paystack.co/transaction/initialize", headers=headers, json=data)
    res_data = response.json()
    return redirect(res_data['data']['authorization_url'])

# Payment callback
def payment_callback(request, freelancer_id):
    reference = request.GET.get('reference')
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    response = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers)
    res_data = response.json()

    if res_data['status'] and res_data['data']['status'] == 'success':
        amount = res_data['data']['amount'] / 100
        freelancer = get_object_or_404(FreelancerProfile, id=freelancer_id)
        commission = amount * 0.10
        Payment.objects.create(
            freelancer=freelancer,
            client_name=request.user.username,
            amount_paid=amount,
            commission=commission,
            reference=reference
        )
        return render(request, 'marketplace/payment_success.html', {'freelancer': freelancer, 'amount': amount, 'commission': commission})
    return render(request, 'marketplace/payment_failed.html')
