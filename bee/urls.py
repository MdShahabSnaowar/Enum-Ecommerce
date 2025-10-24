# urls.py (Create this file in your app directory)
from django.urls import path
from .views import *
from . import views
from django.urls import path, include
from rest_framework.routers import DefaultRouter


urlpatterns = [
    path('v1/auth/register', RegisterAPIView.as_view(), name='register'),
    path('v1/auth/verify-email', VerifyOTPAPIView.as_view(), name='verify-otp'),
    path('v1/auth/login', LoginAPIView.as_view(), name='login'),
    path('v1/my-profile', MyProfileView.as_view(), name='my-profile'),
    
    path("auth/google/callback", views.google_callback, name="google_callback"),
    
    
    
    path('categories', CategoryListCreateAPIView.as_view()),
    path('categories/<str:pk>', CategoryDetailAPIView.as_view()),

    path('brands', BrandListCreateAPIView.as_view()),
    path('brands/<uuid:pk>/', BrandDetailAPIView.as_view()),

    path('products/', ProductListCreateAPIView.as_view()),
    path('products/<uuid:pk>/', ProductDetailAPIView.as_view()),

    path('variants/', VariantListCreateAPIView.as_view()),
    path('variants/<uuid:pk>/', VariantDetailAPIView.as_view()),

    path('warehouses/', WarehouseListCreateAPIView.as_view()),
    path('warehouses/<uuid:pk>/', WarehouseDetailAPIView.as_view()),

    path('inventories/', InventoryListCreateAPIView.as_view()),
    path('inventories/<uuid:pk>/', InventoryDetailAPIView.as_view()),

    path('purchase-orders/', PurchaseOrderListCreateAPIView.as_view()),
    path('purchase-orders/<uuid:pk>/', PurchaseOrderDetailAPIView.as_view()),

    path('purchase-order-items/', PurchaseOrderItemListCreateAPIView.as_view()),
    path('purchase-order-items/<uuid:pk>/', PurchaseOrderItemDetailAPIView.as_view()),
]