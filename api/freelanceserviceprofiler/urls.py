from django.urls import path
from . import views

urlpatterns = [
    path('profile/create/', views.profile_create, name='profile_create'),
    path('profile/<int:pk>/', views.profile_detail, name='profile_detail'),
    path('freelancers/', views.freelancer_list, name='freelancer_list'),
    path('pay/<int:freelancer_id>/', views.paystack_payment, name='paystack_payment'),
    path('payment/callback/<int:freelancer_id>/', views.payment_callback, name='payment_callback'),
]
