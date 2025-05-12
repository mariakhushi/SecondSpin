from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Product)
admin.site.register(CartItem)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(UserProfile)
admin.site.register(ProductRent)
admin.site.register(RentalOrderItem)
admin.site.register(RentalOrder)


admin.site.index_title = "Welcome to the SecondSpin Shop Admin"
admin.site.site_title = "SecondSpin Admin Portal"
admin.site.site_header = "SecondSpin Shop Admin"
