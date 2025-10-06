from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# -----------------------------
# Basic timestamped abstract
# -----------------------------
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# -----------------------------
# Custom User (extensible)
# -----------------------------
class User(AbstractUser, TimeStampedModel):
    # username, email, password come from AbstractUser
    phone = models.CharField(max_length=20, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, null=True)
    is_seller = models.BooleanField(default=False)
    # other flags

    def __str__(self):
        return self.get_full_name() or self.username


class Address(TimeStampedModel):
    user = models.ForeignKey(User, related_name='addresses', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    address_line1 = models.CharField(max_length=500)
    address_line2 = models.CharField(max_length=500, blank=True, null=True)
    city = models.CharField(max_length=200)
    state = models.CharField(max_length=200)
    pincode = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='India')
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.pincode}"


# -----------------------------
# Catalog: Category -> Brand -> Product -> Variant
# -----------------------------
class Category(TimeStampedModel):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', related_name='children', on_delete=models.SET_NULL, blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name


class Brand(TimeStampedModel):
    name = models.CharField(max_length=200)
    logo = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    seller = models.ForeignKey('Seller', related_name='products', on_delete=models.SET_NULL, blank=True, null=True)
    brand = models.ForeignKey(Brand, related_name='products', on_delete=models.SET_NULL, blank=True, null=True)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.SET_NULL, blank=True, null=True)
    title = models.CharField(max_length=500)
    short_description = models.CharField(max_length=1000, blank=True, null=True)
    long_description = models.TextField(blank=True, null=True)
    specifications = models.JSONField(blank=True, null=True)
    thumbnail = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=['title'])]

    def __str__(self):
        return self.title


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    url = models.URLField()
    alt_text = models.CharField(max_length=255, blank=True, null=True)


class ProductVariant(TimeStampedModel):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    sku = models.CharField(max_length=200, unique=True)
    attributes = models.JSONField(blank=True, null=True)  # e.g. {"color":"red","ram":"8GB"}
    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    weight_grams = models.IntegerField(blank=True, null=True)
    stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.product.title} - {self.sku}"


# -----------------------------
# Seller & Inventory
# -----------------------------
class Seller(TimeStampedModel):
    user = models.OneToOneField(User, related_name='seller_profile', on_delete=models.CASCADE)
    store_name = models.CharField(max_length=255)
    gst_number = models.CharField(max_length=50, blank=True, null=True)
    pan_number = models.CharField(max_length=50, blank=True, null=True)
    bank_account = models.CharField(max_length=255, blank=True, null=True)
    ifsc_code = models.CharField(max_length=50, blank=True, null=True)
    address = models.ForeignKey(Address, related_name='seller_addresses', on_delete=models.SET_NULL, blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    verified = models.BooleanField(default=False)

    def __str__(self):
        return self.store_name


class Warehouse(TimeStampedModel):
    name = models.CharField(max_length=255)
    address = models.TextField()
    pincode = models.CharField(max_length=20)
    capacity = models.BigIntegerField(blank=True, null=True)

    def __str__(self):
        return self.name


class Inventory(TimeStampedModel):
    product_variant = models.ForeignKey(ProductVariant, related_name='inventories', on_delete=models.CASCADE)
    seller = models.ForeignKey(Seller, related_name='inventories', on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, related_name='inventories', on_delete=models.SET_NULL, blank=True, null=True)
    stock_available = models.IntegerField(default=0)
    reserved_stock = models.IntegerField(default=0)
    last_updated = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ('product_variant', 'seller', 'warehouse')


# -----------------------------
# Cart & Wishlist
# -----------------------------
class Cart(TimeStampedModel):
    user = models.OneToOneField(User, related_name='cart', on_delete=models.CASCADE)


class CartItem(TimeStampedModel):
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_time = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ('cart', 'product_variant')


class Wishlist(TimeStampedModel):
    user = models.ForeignKey(User, related_name='wishlists', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, default='My Wishlist')


class WishlistItem(TimeStampedModel):
    wishlist = models.ForeignKey(Wishlist, related_name='items', on_delete=models.CASCADE)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('wishlist', 'product_variant')


# -----------------------------
# Orders & Payments
# -----------------------------
class Order(TimeStampedModel):
    STATUS_CHOICES = [
        ('PLACED', 'Placed'),
        ('CONFIRMED', 'Confirmed'),
        ('PACKED', 'Packed'),
        ('SHIPPED', 'Shipped'),
        ('OUT_FOR_DELIVERY', 'Out for delivery'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
        ('RETURNED', 'Returned'),
    ]

    user = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PLACED')
    placed_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Order #{self.id} by {self.user_id}"


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product_variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, blank=True, null=True)
    seller = models.ForeignKey(Seller, related_name='order_items', on_delete=models.SET_NULL, blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=50, default='ORDERED')


class Payment(TimeStampedModel):
    METHOD_CHOICES = [
        ('RAZORPAY', 'Razorpay'),
        ('CARD', 'Card'),
        ('UPI', 'UPI'),
        ('WALLET', 'Wallet'),
        ('COD', 'Cash on Delivery'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]

    order = models.OneToOneField(Order, related_name='payment', on_delete=models.CASCADE)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    gateway = models.CharField(max_length=255, blank=True, null=True)
    transaction_id = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    paid_at = models.DateTimeField(blank=True, null=True)


class Refund(TimeStampedModel):
    order = models.ForeignKey(Order, related_name='refunds', on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, related_name='refunds', on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, default='REQUESTED')


# -----------------------------
# Shipping & Delivery
# -----------------------------
class DeliveryAgent(TimeStampedModel):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30)
    vehicle_number = models.CharField(max_length=100, blank=True, null=True)
    area_assigned = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name


class Shipment(TimeStampedModel):
    order = models.OneToOneField(Order, related_name='shipment', on_delete=models.CASCADE)
    tracking_number = models.CharField(max_length=255, blank=True, null=True)
    carrier_name = models.CharField(max_length=255, blank=True, null=True)
    estimated_delivery = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=80, default='CREATED')
    delivery_agent = models.ForeignKey(DeliveryAgent, related_name='shipments', on_delete=models.SET_NULL, blank=True, null=True)


class DeliveryLog(TimeStampedModel):
    shipment = models.ForeignKey(Shipment, related_name='logs', on_delete=models.CASCADE)
    status = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=255, blank=True, null=True)


# -----------------------------
# Reviews & Ratings
# -----------------------------
class ProductReview(TimeStampedModel):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='product_reviews', on_delete=models.SET_NULL, blank=True, null=True)
    rating = models.PositiveSmallIntegerField()
    review_text = models.TextField(blank=True, null=True)
    images = models.JSONField(blank=True, null=True)
    is_verified_purchase = models.BooleanField(default=False)


class SellerReview(TimeStampedModel):
    seller = models.ForeignKey(Seller, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='seller_reviews', on_delete=models.SET_NULL, blank=True, null=True)
    rating = models.PositiveSmallIntegerField()
    review_text = models.TextField(blank=True, null=True)


# -----------------------------
# Promotions: Coupons, Offers, SuperCoins
# -----------------------------
class Coupon(TimeStampedModel):
    code = models.CharField(max_length=100, unique=True)
    discount_type = models.CharField(max_length=20, choices=[('PERCENT','Percent'),('FLAT','Flat')])
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)


class AppliedCoupon(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True)


class SuperCoin(TimeStampedModel):
    user = models.OneToOneField(User, related_name='supercoin_wallet', on_delete=models.CASCADE)
    balance = models.BigIntegerField(default=0)


class SuperCoinHistory(TimeStampedModel):
    ACTION_CHOICES = [
        ('EARN','Earn'),
        ('REDEEM','Redeem'),
        ('EXPIRE','Expire')
    ]
    user = models.ForeignKey(User, related_name='supercoin_history', on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    coins = models.BigIntegerField()
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, blank=True, null=True)
    note = models.TextField(blank=True, null=True)


# -----------------------------
# Support, Notifications & Analytics
# -----------------------------
class SupportTicket(TimeStampedModel):
    STATUS = [('OPEN','Open'),('PENDING','Pending'),('RESOLVED','Resolved'),('CLOSED','Closed')]
    user = models.ForeignKey(User, related_name='tickets', on_delete=models.CASCADE)
    order = models.ForeignKey(Order, related_name='tickets', on_delete=models.SET_NULL, blank=True, null=True)
    subject = models.CharField(max_length=500)
    message = models.TextField()
    status = models.CharField(max_length=30, choices=STATUS, default='OPEN')


class TicketReply(TimeStampedModel):
    ticket = models.ForeignKey(SupportTicket, related_name='replies', on_delete=models.CASCADE)
    sender_type = models.CharField(max_length=30)  # 'user' or 'support' or 'seller'
    message = models.TextField()


class Notification(TimeStampedModel):
    user = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=100, blank=True, null=True)
    read = models.BooleanField(default=False)


class PageView(TimeStampedModel):
    user = models.ForeignKey(User, related_name='page_views', on_delete=models.SET_NULL, blank=True, null=True)
    product = models.ForeignKey(Product, related_name='page_views', on_delete=models.SET_NULL, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    device_type = models.CharField(max_length=100, blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)


class SearchLog(TimeStampedModel):
    user = models.ForeignKey(User, related_name='search_logs', on_delete=models.SET_NULL, blank=True, null=True)
    query = models.CharField(max_length=1000)
    timestamp = models.DateTimeField(auto_now_add=True)


class ErrorLog(TimeStampedModel):
    module = models.CharField(max_length=255)
    error_message = models.TextField()
    stack_trace = models.TextField(blank=True, null=True)


# -----------------------------
# Small helpers and signals would be defined elsewhere (e.g., wallet updates, stock reservations)
# This file focuses on data models only.
# -----------------------------
