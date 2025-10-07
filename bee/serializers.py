# serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *
import random
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

class RegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def create(self, validated_data):
        user = User.objects.create(
            full_name=validated_data['full_name'],
            email=validated_data['email'],
            username=validated_data['email'],  
            is_active=False  
        )
        user.set_password(validated_data['password'])
        user.save()

        
        otp_code = str(random.randint(100000, 999999))
        OTP.objects.update_or_create(user=user, defaults={'otp_code': otp_code})

        
        from django.core.mail import send_mail
        from django.conf import settings

        subject = 'Your OTP for Registration'
        message = f'Your OTP is {otp_code}. It will expire in 5 minutes.'
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

        return user

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        email = data['email']
        otp = data['otp']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        try:
            otp_obj = OTP.objects.get(user=user, otp_code=otp)
        except OTP.DoesNotExist:
            raise serializers.ValidationError("Invalid OTP.")

        if otp_obj.is_expired():
            otp_obj.delete()
            raise serializers.ValidationError("OTP has expired.")
        
        try:
            user_role = Role.objects.get(name='user')
            user.role = user_role
        except Role.DoesNotExist:
            raise serializers.ValidationError("User role not found.")


        user.is_active = True
        user.save()
        otp_obj.delete()  

        return data
    
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        try:
            
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")

        
        if not user.check_password(password):
            raise serializers.ValidationError("Invalid email or password.")

        
        if not user.is_active:
            raise serializers.ValidationError("User account is not active.")

        
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        
        access_token["user_id"] = str(user.id)
        access_token["email"] = user.email
        access_token["full_name"] = user.full_name or ""
        access_token["phone"] = user.phone or ""
        access_token["dob"] = user.dob.isoformat() if user.dob else None
        access_token["gender"] = user.gender or ""
        access_token["is_seller"] = user.is_seller
        access_token["role"] = user.role.name if user.role else None
        access_token["profile_verified"] = True

        data["user"] = user
        data["refresh"] = str(refresh)
        data["access"] = str(access_token)

        return data