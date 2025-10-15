# urls.py (Create this file in your app directory)
from django.urls import path
from .views import *
from . import views

urlpatterns = [
    path('v1/auth/register', RegisterAPIView.as_view(), name='register'),
    path('v1/auth/verify-email', VerifyOTPAPIView.as_view(), name='verify-otp'),
    path('v1/auth/login', LoginAPIView.as_view(), name='login'),
    path('v1/my-profile', MyProfileView.as_view(), name='my-profile'),
    
    path("auth/google/callback", views.google_callback, name="google_callback"),
]