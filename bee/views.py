from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, VerifyOTPSerializer, LoginSerializer
from datetime import timedelta

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