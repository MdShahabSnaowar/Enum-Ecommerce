from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, VerifyOTPSerializer, LoginSerializer
from datetime import timedelta
from django.shortcuts import redirect
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
import requests
from .models import *
import os

class RegisterAPIView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    
                    "message": "User registered. OTP sent to email.",
                    "meta": {
                        
                            "user_id": str(user.id),
                            "email": user.email,
                            "full_name": user.full_name
                        
                    },
                    "error": False
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            {
                
                "message": serializer.errors,
                "meta": {
                    
                },
                "error": True,
            },
            status=status.HTTP_400_BAD_REQUEST
        )

class VerifyOTPAPIView(APIView):
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            return Response(
                {
                    "error": False,
                    "message": "OTP verified. User activated.",
                    "meta": {
                        "data": {
                            "email": serializer.validated_data['email']
                        }
                    }
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {
                "error": True,
                "message": "OTP verification failed.",
                "meta": {
                    "data": serializer.errors
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )

class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            access_token = serializer.validated_data['access']
            refresh_token = serializer.validated_data['refresh']

            
            response = Response(
                {
                    
                    "message": "Login successful.",
                    "meta": {
                            "access_token": str(access_token),
                            "refresh_token": str(refresh_token),
                            "user_id": str(user.id),
                            "email": user.email,
                            "full_name": user.full_name or '',
                            "profile_verified": True
                        
                    },
                    "error": False,
                },
                status=status.HTTP_200_OK
            )

            # Set cookies
            response.set_cookie(
                key='access_token',
                value=access_token,
                max_age=timedelta(minutes=60).total_seconds(),  
                secure=True,  
                httponly=True, 
                samesite='Lax'  
            )
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                max_age=timedelta(days=1).total_seconds(),  
                secure=True,
                httponly=True,
                samesite='Lax'
            )

            return response
        return Response(
            {
                
                "message": serializer.errors,
                "meta": {},
                "error": True,
            },
            status=status.HTTP_400_BAD_REQUEST
        )
        
        
        
def generate_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
        
def google_callback(request):
    code = request.GET.get("code")
    if not code:
        return JsonResponse({"error": "Missing authorization code"}, status=400)

    try:
        # 1️⃣ Exchange code for access token
        token_data = {
            "code": code,
            "client_id": os.getenv("GOOGLE_CLIENT_ID"),
            "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
            "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI"),
            "grant_type": "authorization_code",
        }

        token_res = requests.post(
            "https://oauth2.googleapis.com/token",
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        token_json = token_res.json()
        print("🔹 TOKEN RESPONSE:", token_json)
        access_token = token_json.get("access_token")
        if not access_token:
            return JsonResponse({"error": "Access token not found"}, status=400)

        # 2️⃣ Get user info
        user_info_res = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        user_info = user_info_res.json()

        # 3️⃣ Find or create user
        user, created = User.objects.get_or_create(
            email=user_info["email"],
            defaults={
                "first_name": user_info.get("given_name", "First"),
                "last_name": user_info.get("family_name", "Last"),
                "profile_picture": user_info.get("picture", ""),
                "auth_provider": "google",
            },
        )

        # 4️⃣ Generate JWT tokens
        jwt_tokens = generate_tokens(user)

        # 5️⃣ Redirect to frontend with query params
        query = (
            f"access_token={jwt_tokens['access']}"
            f"&refresh_token={jwt_tokens['refresh']}"
            f"&email={user.email}"
            f"&user_id={user.id}"
        )
        redirect_url = f"http://127.0.0.1:8000/success?{query}"

        return redirect(redirect_url)

    except Exception as e:
        print("Google login error:", str(e))
        return JsonResponse({"error": "Google authentication failed"}, status=400)
