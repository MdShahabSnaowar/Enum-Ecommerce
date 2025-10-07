# urls.py (Create this file in your app directory)
from django.urls import path
from .views import *

urlpatterns = [
    path('user-register', RegisterAPIView.as_view(), name='register'),
    path('user-verify-otp', VerifyOTPAPIView.as_view(), name='verify-otp'),
    path('user-login', LoginAPIView.as_view(), name='login'),
]