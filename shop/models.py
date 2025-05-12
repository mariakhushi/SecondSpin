from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date


# User Profile to extend the default User model
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)

    def __str__(self):
        return self.user.username


# Product model
class Product(models.Model):
    CATEGORY_CHOICES = [
    ('Kids', 'Kids'),
    ('Women', 'Women'),
    ('Men', 'Men'),
    ('Thrifting Clothes', 'Thrifting Clothes'),
    ('Summer Collection', 'Summer Collection'),]
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    stock = models.PositiveIntegerField(default=1)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name

# Cart Item model
class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')

    def __str__(self):
        return f"{self.quantity} of {self.product.name}"

    def get_total_price(self):
        return self.quantity * self.product.price

# Order model
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('Pending', 'Pending'),
            ('Confirmed', 'Confirmed'),
            ('Shipped', 'Shipped'),
            ('Delivered', 'Delivered'),
            ('Cancelled', 'Cancelled'),
        ],
        default='Pending'
    )
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ('Bkash', 'Bkash'),
            ('Nagad', 'Nagad'),
            ('Cash on Delivery', 'Cash on Delivery'),
        ],
        default='Cash on Delivery'
    )
    

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

# Order Item model
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} of {self.product.name} in Order {self.order.id}"
    

# Product Rent model
class ProductRent(models.Model):
    CATEGORY_CHOICES = [
        ('men', 'Men'),
        ('women', 'Women'),
        ('kids', 'Kids'),
        ('winter', 'Winter Collection'),
        ('summer', 'Summer Collection'),
        ('formal', 'Formal Wear'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    image = models.ImageField(upload_to='rental_products/')
    size = models.CharField(max_length=50)  # Example: S, M, L, XL, Custom size descriptions
    rent_price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=1, help_text="Number of available items for rent")
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title  

# Rental Order model
class RentalOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rental_orders')
    product = models.ForeignKey(ProductRent, on_delete=models.CASCADE, related_name='rental_orders')
    rental_start_date = models.DateField()
    rental_end_date = models.DateField()
    total_rent_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('Pending', 'Pending'),
            ('Confirmed', 'Confirmed'),
            ('Returned', 'Returned'),
            ('Cancelled', 'Cancelled'),
        ],
        default='Pending'
    )

    def clean(self):
        if self.rental_end_date <= self.rental_start_date:
            raise ValidationError("Rental end date must be after the start date.")

    def save(self, *args, **kwargs):
        # Calculate total rental price
        rental_days = (self.rental_end_date - self.rental_start_date).days
        self.total_rent_price = rental_days * self.product.rent_price_per_day

        # Reduce stock only when order is confirmed
        if self.status == 'Confirmed' and self.product.stock > 0:
            self.product.stock -= 1
            self.product.save()

        # Return stock when order is returned
        if self.status == 'Returned':
            self.product.stock += 1
            self.product.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Rental Order {self.id} by {self.user.username}"    

# Rental Order Item model
class RentalOrderItem(models.Model):
    rental_order = models.ForeignKey(RentalOrder, on_delete=models.CASCADE, related_name='rental_items')
    product = models.ForeignKey(ProductRent, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    rent_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} of {self.product.title} in Rental Order {self.rental_order.id}"

