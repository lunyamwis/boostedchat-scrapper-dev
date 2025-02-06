from django.urls import path, include
from . import views

urlpatterns = [
    path('test-account/', views.TestAccount.as_view()),
]

