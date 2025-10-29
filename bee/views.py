from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RegisterSerializer, VerifyOTPSerializer, LoginSerializer,UserProfileSerializer
from datetime import timedelta
from django.shortcuts import redirect
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
import requests
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from .models import *
from . serializers import *
import os

class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")

        # ✅ Check if user already exists
        existing_user = User.objects.filter(email=email).first()

        if existing_user:
            if existing_user.profile_verified:
                # Already verified user
                return Response(
                    {
                        "message": "User already registered and verified.",
                        "meta": {"email": existing_user.email},
                        "error": True,
                    },
                    status=status.HTTP_200_OK
                )
            else:
                # ✅ Re-send OTP logic (you can reuse your existing OTP send function)
                # send_otp_to_email(existing_user.email)
                return Response(
                    {
                        "message": "User already exists but not verified. OTP re-sent to email.",
                        "meta": {"email": existing_user.email},
                        "error": False,
                    },
                    status=status.HTTP_200_OK
                )

        # ✅ If no user exists — create a new one
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # send_otp_to_email(user.email)
            return Response(
                {
                    "message": "User registered successfully. OTP sent to email.",
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
                "meta": {},
                "error": True,
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class VerifyOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response(
                    {"error": True, "message": "User not found.", "meta": {}},
                    status=status.HTTP_404_NOT_FOUND
                )

            # ✅ Mark user verified
            user.is_active = True
            user.profile_verified = True
            user.save()

            # ✅ Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # ✅ Prepare response
            response = Response(
                {
                    "error": False,
                    "message": "OTP verified successfully. User activated.",
                    "meta": {
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "user_id": str(user.id),
                        "email": user.email,
                        "full_name": user.full_name or '',
                    },
                },
                status=status.HTTP_200_OK
            )

            # ✅ Set cookies
            response.set_cookie(
                key='access_token',
                value=access_token,
                max_age=timedelta(minutes=60).total_seconds(),
                secure=False,  # True in production
                httponly=True,
                samesite='None'
            )
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                max_age=timedelta(days=1).total_seconds(),
                secure=False,
                httponly=True,
                samesite='None'
            )

            return response

        return Response(
            {
                "error": True,
                "message": "OTP verification failed.",
                "meta": {"data": serializer.errors}
            },
            status=status.HTTP_400_BAD_REQUEST
        )



class LoginAPIView(APIView):
    authentication_classes = []  # Disable token auth
    permission_classes = [AllowAny]
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
                secure=False,  
                httponly=True, 
                samesite='None'
            )
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                max_age=timedelta(days=1).total_seconds(),  
                secure=False,
                httponly=True,
                samesite='None'
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



class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]  # ensures token validated by JWTAuthentication

    def get(self, request):
        user = request.user
        serializer = UserProfileSerializer(user)
        return Response({
            "message": "User profile fetched successfully.",
            "meta": serializer.data,
            "error": True,
            
        })
        
        
        
def api_response(message, error, data=None, code=status.HTTP_200_OK):
    return Response({
        "message": message,
        "error": error,
        "meta": {"data": data if data else {}}
    }, status=code)


# ---------- CATEGORY ----------
from .utils import is_admin_from_token  # your admin token checker


# ✅ Common Mixin for Admin Authentication
class AdminAuthMixin:
    def check_admin(self, request):
        """
        Verifies that the provided token belongs to an admin user.
        Raises AuthenticationFailed if unauthorized.
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise AuthenticationFailed("Authorization token missing or invalid format")

        token = auth_header.split(" ")[1]
        is_admin, user = is_admin_from_token(token)
        if not is_admin:
            raise AuthenticationFailed("Access denied — admin privileges required")
        return user


# ---------------- CATEGORY ----------------
class CategoryListCreateAPIView(AdminAuthMixin, APIView):
    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return api_response("Categories fetched successfully", False, serializer.data)

    def post(self, request):
        self.check_admin(request)
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response("Category created successfully", False, serializer.data, status.HTTP_201_CREATED)
        return api_response("Validation failed", True, serializer.errors, status.HTTP_400_BAD_REQUEST)


class CategoryDetailAPIView(AdminAuthMixin, APIView):
    def get(self, request, pk):
        try:
            category = Category.objects.get(pk=pk)
            serializer = CategorySerializer(category)
            return api_response("Category details fetched", False, serializer.data)
        except Category.DoesNotExist:
            return api_response("Category not found", True, {}, status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        self.check_admin(request)
        try:
            category = Category.objects.get(pk=pk)
            serializer = CategorySerializer(category, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return api_response("Category updated successfully", False, serializer.data)
            return api_response("Validation failed", True, serializer.errors, status.HTTP_400_BAD_REQUEST)
        except Category.DoesNotExist:
            return api_response("Category not found", True, {}, status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        self.check_admin(request)
        try:
            category = Category.objects.get(pk=pk)
            category.delete()
            return api_response("Category deleted successfully", False)
        except Category.DoesNotExist:
            return api_response("Category not found", True, {}, status.HTTP_404_NOT_FOUND)


# ---------------- BRAND ----------------
class BrandListCreateAPIView(AdminAuthMixin, APIView):
    def get(self, request):
        brands = Brand.objects.all()
        serializer = BrandSerializer(brands, many=True)
        return api_response("Brands fetched successfully", False, serializer.data)

    def post(self, request):
        self.check_admin(request)
        serializer = BrandSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response("Brand created successfully", False, serializer.data, status.HTTP_201_CREATED)
        return api_response("Validation failed", True, serializer.errors, status.HTTP_400_BAD_REQUEST)


class BrandDetailAPIView(AdminAuthMixin, APIView):
    def get(self, request, pk):
        try:
            brand = Brand.objects.get(pk=pk)
            serializer = BrandSerializer(brand)
            return api_response("Brand details fetched", False, serializer.data)
        except Brand.DoesNotExist:
            return api_response("Brand not found", True, {}, status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        self.check_admin(request)
        try:
            brand = Brand.objects.get(pk=pk)
            serializer = BrandSerializer(brand, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return api_response("Brand updated successfully", False, serializer.data)
            return api_response("Validation failed", True, serializer.errors, status.HTTP_400_BAD_REQUEST)
        except Brand.DoesNotExist:
            return api_response("Brand not found", True, {}, status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        self.check_admin(request)
        try:
            brand = Brand.objects.get(pk=pk)
            brand.delete()
            return api_response("Brand deleted successfully", False)
        except Brand.DoesNotExist:
            return api_response("Brand not found", True, {}, status.HTTP_404_NOT_FOUND)


# ---------------- PRODUCT ----------------
class ProductListCreateAPIView(AdminAuthMixin, APIView):
    def get(self, request):
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return api_response("Products fetched successfully", False, serializer.data)

    def post(self, request):
        self.check_admin(request)
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response("Product created successfully", False, serializer.data, status.HTTP_201_CREATED)
        return api_response("Validation failed", True, serializer.errors, status.HTTP_400_BAD_REQUEST)


class ProductDetailAPIView(AdminAuthMixin, APIView):
    def get(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
            serializer = ProductSerializer(product)
            return api_response("Product details fetched", False, serializer.data)
        except Product.DoesNotExist:
            return api_response("Product not found", True, {}, status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        self.check_admin(request)
        try:
            product = Product.objects.get(pk=pk)
            serializer = ProductSerializer(product, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return api_response("Product updated successfully", False, serializer.data)
            return api_response("Validation failed", True, serializer.errors, status.HTTP_400_BAD_REQUEST)
        except Product.DoesNotExist:
            return api_response("Product not found", True, {}, status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        self.check_admin(request)
        try:
            product = Product.objects.get(pk=pk)
            product.delete()
            return api_response("Product deleted successfully", False)
        except Product.DoesNotExist:
            return api_response("Product not found", True, {}, status.HTTP_404_NOT_FOUND)


# ---------------- VARIANT ----------------
class VariantListCreateAPIView(AdminAuthMixin, APIView):
    def get(self, request):
        variants = Variant.objects.all()
        serializer = VariantSerializer(variants, many=True)
        return api_response("Variants fetched successfully", False, serializer.data)

    def post(self, request):
        self.check_admin(request)
        serializer = VariantSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response("Variant created successfully", False, serializer.data, status.HTTP_201_CREATED)
        return api_response("Validation failed", True, serializer.errors, status.HTTP_400_BAD_REQUEST)


class VariantDetailAPIView(AdminAuthMixin, APIView):
    def get(self, request, pk):
        try:
            variant = Variant.objects.get(pk=pk)
            serializer = VariantSerializer(variant)
            return api_response("Variant details fetched", False, serializer.data)
        except Variant.DoesNotExist:
            return api_response("Variant not found", True, {}, status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        self.check_admin(request)
        try:
            variant = Variant.objects.get(pk=pk)
            serializer = VariantSerializer(variant, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return api_response("Variant updated successfully", False, serializer.data)
            return api_response("Validation failed", True, serializer.errors, status.HTTP_400_BAD_REQUEST)
        except Variant.DoesNotExist:
            return api_response("Variant not found", True, {}, status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        self.check_admin(request)
        try:
            variant = Variant.objects.get(pk=pk)
            variant.delete()
            return api_response("Variant deleted successfully", False)
        except Variant.DoesNotExist:
            return api_response("Variant not found", True, {}, status.HTTP_404_NOT_FOUND)


# ---------------- WAREHOUSE ----------------
class WarehouseListCreateAPIView(AdminAuthMixin, APIView):
    def get(self, request):
        warehouses = Warehouse.objects.all()
        serializer = WarehouseSerializer(warehouses, many=True)
        return api_response("Warehouses fetched successfully", False, serializer.data)

    def post(self, request):
        self.check_admin(request)
        serializer = WarehouseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response("Warehouse created successfully", False, serializer.data, status.HTTP_201_CREATED)
        return api_response("Validation failed", True, serializer.errors, status.HTTP_400_BAD_REQUEST)


class WarehouseDetailAPIView(AdminAuthMixin, APIView):
    def get(self, request, pk):
        try:
            warehouse = Warehouse.objects.get(pk=pk)
            serializer = WarehouseSerializer(warehouse)
            return api_response("Warehouse details fetched", False, serializer.data)
        except Warehouse.DoesNotExist:
            return api_response("Warehouse not found", True, {}, status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        self.check_admin(request)
        try:
            warehouse = Warehouse.objects.get(pk=pk)
            serializer = WarehouseSerializer(warehouse, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return api_response("Warehouse updated successfully", False, serializer.data)
            return api_response("Validation failed", True, serializer.errors, status.HTTP_400_BAD_REQUEST)
        except Warehouse.DoesNotExist:
            return api_response("Warehouse not found", True, {}, status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        self.check_admin(request)
        try:
            warehouse = Warehouse.objects.get(pk=pk)
            warehouse.delete()
            return api_response("Warehouse deleted successfully", False)
        except Warehouse.DoesNotExist:
            return api_response("Warehouse not found", True, {}, status.HTTP_404_NOT_FOUND)


# ---------------- INVENTORY ----------------
class InventoryListCreateAPIView(AdminAuthMixin, APIView):
    def get(self, request):
        inventories = Inventory.objects.all()
        serializer = InventorySerializer(inventories, many=True)
        return api_response("Inventories fetched successfully", False, serializer.data)

    def post(self, request):
        self.check_admin(request)
        serializer = InventorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response("Inventory created successfully", False, serializer.data, status.HTTP_201_CREATED)
        return api_response("Validation failed", True, serializer.errors, status.HTTP_400_BAD_REQUEST)


class InventoryDetailAPIView(AdminAuthMixin, APIView):
    def get(self, request, pk):
        try:
            inventory = Inventory.objects.get(pk=pk)
            serializer = InventorySerializer(inventory)
            return api_response("Inventory details fetched", False, serializer.data)
        except Inventory.DoesNotExist:
            return api_response("Inventory not found", True, {}, status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        self.check_admin(request)
        try:
            inventory = Inventory.objects.get(pk=pk)
            serializer = InventorySerializer(inventory, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return api_response("Inventory updated successfully", False, serializer.data)
            return api_response("Validation failed", True, serializer.errors, status.HTTP_400_BAD_REQUEST)
        except Inventory.DoesNotExist:
            return api_response("Inventory not found", True, {}, status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        self.check_admin(request)
        try:
            inventory = Inventory.objects.get(pk=pk)
            inventory.delete()
            return api_response("Inventory deleted successfully", False)
        except Inventory.DoesNotExist:
            return api_response("Inventory not found", True, {}, status.HTTP_404_NOT_FOUND)


# ---------------- PURCHASE ORDER ----------------
class PurchaseOrderListCreateAPIView(AdminAuthMixin, APIView):
    def get(self, request):
        orders = PurchaseOrder.objects.all()
        serializer = PurchaseOrderSerializer(orders, many=True)
        return api_response("Purchase orders fetched successfully", False, serializer.data)

    def post(self, request):
        self.check_admin(request)
        serializer = PurchaseOrderSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response("Purchase order created successfully", False, serializer.data, status.HTTP_201_CREATED)
        return api_response("Validation failed", True, serializer.errors, status.HTTP_400_BAD_REQUEST)


class PurchaseOrderDetailAPIView(AdminAuthMixin, APIView):
    def get(self, request, pk):
        try:
            order = PurchaseOrder.objects.get(pk=pk)
            serializer = PurchaseOrderSerializer(order)
            return api_response("Purchase order details fetched", False, serializer.data)
        except PurchaseOrder.DoesNotExist:
            return api_response("Purchase order not found", True, {}, status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        self.check_admin(request)
        try:
            order = PurchaseOrder.objects.get(pk=pk)
            serializer = PurchaseOrderSerializer(order, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return api_response("Purchase order updated successfully", False, serializer.data)
            return api_response("Validation failed", True, serializer.errors, status.HTTP_400_BAD_REQUEST)
        except PurchaseOrder.DoesNotExist:
            return api_response("Purchase order not found", True, {}, status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        self.check_admin(request)
        try:
            order = PurchaseOrder.objects.get(pk=pk)
            order.delete()
            return api_response("Purchase order deleted successfully", False)
        except PurchaseOrder.DoesNotExist:
            return api_response("Purchase order not found", True, {}, status.HTTP_404_NOT_FOUND)


# ---------------- PURCHASE ORDER ITEM ----------------
class PurchaseOrderItemListCreateAPIView(AdminAuthMixin, APIView):
    def get(self, request):
        items = PurchaseOrderItem.objects.all()
        serializer = PurchaseOrderItemSerializer(items, many=True)
        return api_response("Purchase order items fetched successfully", False, serializer.data)

    def post(self, request):
        self.check_admin(request)
        serializer = PurchaseOrderItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return api_response("Purchase order item created successfully", False, serializer.data, status.HTTP_201_CREATED)
        return api_response("Validation failed", True, serializer.errors, status.HTTP_400_BAD_REQUEST)


class PurchaseOrderItemDetailAPIView(AdminAuthMixin, APIView):
    def get(self, request, pk):
        try:
            item = PurchaseOrderItem.objects.get(pk=pk)
            serializer = PurchaseOrderItemSerializer(item)
            return api_response("Purchase order item details fetched", False, serializer.data)
        except PurchaseOrderItem.DoesNotExist:
            return api_response("Purchase order item not found", True, {}, status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        self.check_admin(request)
        try:
            item = PurchaseOrderItem.objects.get(pk=pk)
            serializer = PurchaseOrderItemSerializer(item, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return api_response("Purchase order item updated successfully", False, serializer.data)
            return api_response("Validation failed", True, serializer.errors, status.HTTP_400_BAD_REQUEST)
        except PurchaseOrderItem.DoesNotExist:
            return api_response("Purchase order item not found", True, {}, status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        self.check_admin(request)
        try:
            item = PurchaseOrderItem.objects.get(pk=pk)
            item.delete()
            return api_response("Purchase order item deleted successfully", False)
        except PurchaseOrderItem.DoesNotExist:
            return api_response("Purchase order item not found", True, {}, status.HTTP_404_NOT_FOUND)
