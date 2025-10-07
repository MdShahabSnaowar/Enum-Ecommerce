from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, VerifyOTPSerializer

class RegisterAPIView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "error": False,
                    "message": "User registered. OTP sent to email.",
                    "meta": {
                        
                            "user_id": str(user.id),
                            "email": user.email,
                            "full_name": user.full_name
                        
                    }
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            {
                
                "message": serializer.errors,
                "meta": {},
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
                    
                    "message": "OTP verified. User activated.",
                    "meta": {
                        "email": serializer.validated_data['email']
                    },
                    "error": False,
                },
                status=status.HTTP_200_OK
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