from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.contrib.auth.models import User
from datetime import datetime
from django.db import transaction


# Create your views here.
def home(request):
    return render(request, 'Home.html')

def SignUp(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username is already taken. Please choose a different username.')
            return render(request, 'signup.html')

       
        user = User.objects.create_user(username=username, email=email, password=password)

        
        request.session['signup_username'] = username
        request.session['signup_email'] = email
        request.session['signup_password'] = password

        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, 'You have successfully signed up!')
            return redirect('login')  
        else:
            messages.error(request, 'An error occurred while signing up. Please try again.')
            return render(request, 'Signup.html')
        
    return render(request, 'Signup.html')

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Check if the login credentials belong to a regular user
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            messages.success(request, 'You have successfully logged in!')
            return redirect('home')  # Redirect to the booking page
         
        else:
            # Authentication failed, display an error message
            messages.error(request, 'Invalid username or password.')
            return redirect('login')
    return render(request, 'login.html')

@login_required
def logout(request):
    django_logout(request)
    return redirect('home')

@login_required
def user_profile(request):
    user = request.user
    try:
        user_profile = user.profile  
    except UserProfile.DoesNotExist:
        
        user_profile = None

    
    products = Product.objects.filter(seller=user) if user_profile else None

    
    orders = Order.objects.filter(user=user) if user_profile else None

    return render(request, 'user_profile.html', {
        'user': user,
        'user_profile': user_profile,
        'products': products,
        'orders': orders
    })


@login_required
def edit_profile(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        profile.phone = request.POST.get('phone', profile.phone)
        profile.address = request.POST.get('address', profile.address)
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('user_profile')

    return render(request, 'edit_profile.html', {'profile': profile})


@login_required
def create_product(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        category = request.POST.get('category')
        stock = request.POST.get('stock')
        image = request.FILES.get('image')

        # Validate required fields
        if not all([name, description, price, category, stock]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('create_product')  

        try:
            price = float(price)  
            stock = int(stock)  
            user = request.user  

            product = Product.objects.create(
                name=name,
                description=description,
                price=price,
                category=category,
                stock=stock,
                image=image,
                seller=user,
            )
            messages.success(request, 'Product created successfully!')
            return redirect('user_profile')
        except ValueError:
            messages.error(request, 'Invalid price or stock value.')
            return redirect('create_product')  

    return render(request, 'create_product.html')


@login_required
def update_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, seller=request.user)

    if request.method == 'POST':
        product.name = request.POST.get('name', product.name)
        product.description = request.POST.get('description', product.description)
        product.price = request.POST.get('price', product.price)
        product.category = request.POST.get('category', product.category)
        product.stock = request.POST.get('stock', product.stock)

        if 'image' in request.FILES:
            product.image = request.FILES['image']

        try:
            product.price = float(product.price)  
            product.stock = int(product.stock)  
            product.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('user_profile')
        except ValueError:
            messages.error(request, 'Invalid price or stock value.')
            return redirect('update_product', product_id=product.id)

    return render(request, 'update_product.html', {'product': product})


@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, seller=request.user)

    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('user_profile')

    return render(request, 'delete_product.html', {'product': product})


@login_required
def seller_products(request):
    products = Product.objects.filter(seller=request.user.profile)
    return render(request, 'seller_products.html', {'products': products})


def shop(request):
    # Get the category filter from the query parameters
    category_filter = request.GET.get('category', None)

    # Filter products based on category if provided, otherwise fetch all products
    if category_filter:
        products = Product.objects.filter(category=category_filter, is_available=True)
    else:
        products = Product.objects.filter(is_available=True)

    # Fetch all unique categories for the filter dropdown
    categories = Product.CATEGORY_CHOICES

    return render(request, 'shop.html', {
        'products': products,
        'categories': categories,
        'selected_category': category_filter,
    })

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'product_detail.html', {'product': product})


@login_required(login_url='login')
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    user = request.user

    # Check if the product is already in the cart
    cart_item, created = CartItem.objects.get_or_create(user=user, product=product)

    if not created:
        # If the item already exists, increase the quantity
        if product.stock > cart_item.quantity:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f"{product.name} quantity increased.")
        else:
            messages.warning(request, "Insufficient stock available.")
    else:
        messages.success(request, f"{product.name} added to cart.")

    return redirect('cart')

@login_required(login_url='login')
def cart(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user)

    # Calculate the total price of items in the cart 
    total_price = cart_items.aggregate(
        total_price=Sum(F('quantity') * F('product__price'))
    )['total_price'] or 0

    return render(request, 'cart.html', {
        'cart_items': cart_items,
        'total_price': total_price,
    })


@login_required
def update_cart_item(request, cart_item_id, action):
    cart_item = get_object_or_404(CartItem, id=cart_item_id, user=request.user)

    if action == 'increase':
        if cart_item.product.stock > cart_item.quantity:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f"Increased quantity of {cart_item.product.name}.")
        else:
            messages.warning(request, "Insufficient stock available.")
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            messages.success(request, f"Decreased quantity of {cart_item.product.name}.")
        else:
            cart_item.delete()
            messages.success(request, f"Removed {cart_item.product.name} from cart.")
    elif action == 'remove':
        cart_item.delete()
        messages.success(request, f"Removed {cart_item.product.name} from cart.")

    return redirect('cart')

@login_required
def checkout(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user).select_related('product')

    if not cart_items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect('cart')

    total_price = float(sum(item.get_total_price() for item in cart_items))

    if request.method == 'POST':
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        payment_method = request.POST.get('payment_method')

        if not address or not phone or not payment_method:
            messages.error(request, "Please fill in all required fields.")
            return redirect('checkout')

        request.session['checkout_address'] = address
        request.session['checkout_phone'] = phone
        request.session['checkout_payment_method'] = payment_method
        request.session['checkout_total_price'] = total_price

        return redirect('confirm_order')

    return render(request, 'checkout.html', {
        'cart_items': cart_items,
        'total_price': total_price,
    })




@login_required
def confirm_order(request):
    user = request.user
    cart_items = CartItem.objects.filter(user=user).select_related('product')

    address = request.session.get('checkout_address')
    phone = request.session.get('checkout_phone')
    total_price = request.session.get('checkout_total_price')
    payment_method = request.session.get('checkout_payment_method')

    if not address or not phone or not total_price or not payment_method:
        messages.error(request, "Checkout details are missing. Please restart the process.")
        return redirect('checkout')

    if request.method == 'POST':
        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=user,
                    total_price=total_price,
                    address=address,
                    phone=phone,
                    payment_method=payment_method
                )

                for item in cart_items:
                    if not item.product:
                        raise Exception("Product not found in cart item.")

                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=item.get_total_price(),
                    )
                    item.product.stock -= item.quantity
                    if item.product.stock <= 0:
                        item.product.is_available = False
                    item.product.save()

                cart_items.delete()

                # Clear session
                for key in ['checkout_address', 'checkout_phone', 'checkout_payment_method', 'checkout_total_price']:
                    request.session.pop(key, None)

                messages.success(request, f"Order placed successfully! Order ID: {order.id}")
                print(f"Order ID: {order.id}")
                return redirect('thanks')

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            print(f"Error: {str(e)}")
            return redirect('checkout')

    return render(request, 'confirm_order.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'address': address,
        'phone': phone,
        'payment_method': payment_method,
    })




@login_required
def thanks(request):
    """Thank you page after order placement."""
    return render(request, 'thanks.html')

@login_required(login_url='login')
def orders(request):
    user = request.user
    orders = Order.objects.filter(user=user).prefetch_related('items__product')

    return render(request, 'orders.html', {'orders': orders})

@login_required(login_url='login')
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_detail.html', {'order': order})

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status == 'Pending':
        # Restore the stock of the products in the order
        for item in order.items.all():
            item.product.stock += item.quantity
            item.product.save()
        
        # Delete the order
        order.delete()
        messages.success(request, 'Order canceled successfully.')
    else:
        messages.error(request, 'Only pending orders can be canceled.')

    return redirect('orders')
        
    

def About(request):
    return render(request, 'About.html')

def Contact(request):
    return render(request, 'Contact.html')




# View Rental Products
def rental_products(request):
    products = ProductRent.objects.filter(available=True)
    return render(request, 'rental_products.html', {'products': products})

# Rental Product Detail Page
def rental_product_detail(request, product_id):
    product = get_object_or_404(ProductRent, id=product_id)
    return render(request, 'rental_product_detail.html', {'product': product})

@login_required
def rental_checkout(request, product_id):
    """Redirects user to the checkout page after selecting rental product"""
    product = get_object_or_404(ProductRent, id=product_id)

    if request.method == 'POST':
        rental_start_date = request.POST.get('rental_start_date')
        rental_end_date = request.POST.get('rental_end_date')

        if not rental_start_date or not rental_end_date:
            messages.error(request, "Please select rental start and end dates.")
            return redirect('rental_product_detail', product_id=product.id)

        # Convert date strings to date objects
        try:
            rental_start_date = datetime.strptime(rental_start_date, '%Y-%m-%d').date()
            rental_end_date = datetime.strptime(rental_end_date, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect('rental_product_detail', product_id=product.id)

        if rental_end_date <= rental_start_date:
            messages.error(request, "Rental end date must be after the start date.")
            return redirect('rental_product_detail', product_id=product.id)

        # Save rental dates in session for use in confirmation
        request.session['rental_start_date'] = rental_start_date.strftime('%Y-%m-%d')
        request.session['rental_end_date'] = rental_end_date.strftime('%Y-%m-%d')

        return redirect('rental_confirm', product_id=product.id)

    return render(request, 'rental_checkout.html', {'product': product})

@login_required
def rental_confirm(request, product_id):
    """Confirm the rental order after checkout"""
    product = get_object_or_404(ProductRent, id=product_id)

    # Retrieve rental dates from session
    rental_start_date = request.session.get('rental_start_date')
    rental_end_date = request.session.get('rental_end_date')

    if not rental_start_date or not rental_end_date:
        messages.error(request, "Rental dates missing. Please restart the process.")
        return redirect('rental_product_detail', product_id=product.id)

    # Convert session string values back to date objects
    rental_start_date = datetime.strptime(rental_start_date, '%Y-%m-%d').date()
    rental_end_date = datetime.strptime(rental_end_date, '%Y-%m-%d').date()

    try:
        with transaction.atomic():
            rental_order = RentalOrder.objects.create(
                user=request.user,
                product=product,
                rental_start_date=rental_start_date,
                rental_end_date=rental_end_date,
                status='Pending'
            )

            messages.success(request, f"Rental Order {rental_order.id} placed successfully!")
            del request.session['rental_start_date']
            del request.session['rental_end_date']

            return redirect('rental_orders')
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('rental_product_detail', product_id=product.id)



# Rental Orders List
@login_required
def rental_orders(request):
    orders = RentalOrder.objects.filter(user=request.user).order_by("-id")
    return render(request, "rental_orders.html", {"orders": orders})

# Cancel Rental Order
@login_required
def cancel_rental_order(request, order_id):
    order = get_object_or_404(RentalOrder, id=order_id, user=request.user)

    if order.status in ["Pending", "Confirmed"]:
        order.status = "Cancelled"
        order.save()
        messages.success(request, "Rental order cancelled successfully.")
    else:
        messages.error(request, "This order cannot be cancelled.")

    return redirect('rental_orders')