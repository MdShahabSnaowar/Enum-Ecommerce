# urls.py (Create this file in your app directory)
from django.urls import path
from .views import RegisterAPIView, VerifyOTPAPIView

urlpatterns = [
    path('user-register', RegisterAPIView.as_view(), name='register'),
    path('user-verify-otp', VerifyOTPAPIView.as_view(), name='verify-otp'),
]