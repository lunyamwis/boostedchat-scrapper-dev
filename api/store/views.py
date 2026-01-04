from django.shortcuts import render, get_object_or_404, redirect
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Review
from django.core.exceptions import ObjectDoesNotExist
import requests
from django.conf import settings
from django.contrib.auth.models import Group, User
from .forms import SignUpForm, ContactForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.template.loader import get_template
from django.core.mail import EmailMessage


def home(request, category_slug=None):
    category_page = None
    products_list = None
    if category_slug != None:
        category_page = get_object_or_404(Category, slug=category_slug)
        products_list = Product.objects.filter(category=category_page, available=True)
    else:
        products_list = Product.objects.all().filter(available=True)

    paginator = Paginator(products_list, 4)

    try:
        page = int(request.GET.get('page', '1'))
    except:
        page = 1

    try:
        products = paginator.page(page)
    except(EmptyPage, InvalidPage):
        products = paginator.page(paginator.num_pages)

    return render(request, 'home.html', {'category': category_page, 'products': products})


def productPage(request, category_slug, product_slug):
    try:
        product = Product.objects.get(category__slug=category_slug, slug=product_slug)
    except Exception as e:
        raise e

    if request.method == 'POST' and request.user.is_authenticated and request.POST['content'].strip() != '':
        Review.objects.create(product=product,
                              user=request.user,
                              content=request.POST['content'])

    reviews = Review.objects.filter(product=product)

    return render(request, 'product.html', {'product': product, 'reviews': reviews})


def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart


def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id=_cart_id(request)
        )
        cart.save()
    try:
        cart_item = CartItem.objects.get(product=product, cart=cart)
        if cart_item.quantity < cart_item.product.stock:
            cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(
            product=product,
            quantity=1,
            cart=cart
        )
        cart_item.save()

    return redirect('cart_detail')



def cart_detail(request, total=0, counter=0, cart_items=None):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            counter += cart_item.quantity
    except ObjectDoesNotExist:
        pass

    paystack_total = int(total * 100)  # Paystack uses kobo
    description = 'Z-Store - New Order'

    if request.method == 'POST':
        email = request.POST.get('email')
        billingName = request.POST.get('billingName')
        billingAddress1 = request.POST.get('billingAddress1')
        billingCity = request.POST.get('billingCity')
        billingPostcode = request.POST.get('billingPostcode')
        billingCountry = request.POST.get('billingCountry')
        shippingName = request.POST.get('shippingName')
        shippingAddress1 = request.POST.get('shippingAddress1')
        shippingCity = request.POST.get('shippingCity')
        shippingPostcode = request.POST.get('shippingPostcode')
        shippingCountry = request.POST.get('shippingCountry')

        # Initialize Paystack transaction
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        callback_url = request.build_absolute_uri('/cart/payment/callback/')  # define callback
        data = {
            "email": email,
            "amount": paystack_total,
            "metadata": {
                "billingName": billingName,
                "billingAddress1": billingAddress1,
                "billingCity": billingCity,
                "billingPostcode": billingPostcode,
                "billingCountry": billingCountry,
                "shippingName": shippingName,
                "shippingAddress1": shippingAddress1,
                "shippingCity": shippingCity,
                "shippingPostcode": shippingPostcode,
                "shippingCountry": shippingCountry
            },
            "callback_url": callback_url
        }
        response = requests.post("https://api.paystack.co/transaction/initialize", headers=headers, json=data)
        res_data = response.json()

        if res_data['status']:
            # Redirect user to Paystack payment page
            return redirect(res_data['data']['authorization_url'])
        else:
            # Handle initialization failure
            return render(request, 'cart.html', {
                "cart_items": cart_items,
                "total": total,
                "counter": counter,
                "error": res_data.get('message')
            })

    return render(request, 'cart.html', {
        "cart_items": cart_items,
        "total": total,
        "counter": counter,
        "paystack_public_key": settings.PAYSTACK_PUBLIC_KEY,
        "paystack_total": paystack_total,
        "description": description
    })


def cart_remove(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart_detail')


def cart_remove_product(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    cart_item.delete()
    return redirect('cart_detail')


def thanks_page(request, order_id):
    if order_id:
        customer_order = get_object_or_404(Order, id=order_id)
    return render(request, 'thankyou.html', {'customer_order': customer_order})


def signupView(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            signup_user = User.objects.get(username=username)
            customer_group = Group.objects.get(name='Customer')
            customer_group.user_set.add(signup_user)
            login(request, signup_user)
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def signinView(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                return redirect('signup')
    else:
        form = AuthenticationForm()
    return render(request, 'signin.html', {'form': form})


def signoutView(request):
    logout(request)
    return redirect('signin')


@login_required(redirect_field_name='next', login_url='signin')
def orderHistory(request):
    if request.user.is_authenticated:
        email = str(request.user.email)
        order_details = Order.objects.filter(emailAddress=email)
        print(email)
        print(order_details)
    return render(request, 'orders_list.html', {'order_details': order_details})


@login_required(redirect_field_name='next', login_url='signin')
def viewOrder(request, order_id):
    if request.user.is_authenticated:
        email = str(request.user.email)
        order = Order.objects.get(id=order_id, emailAddress=email)
        order_items = OrderItem.objects.filter(order=order)
    return render(request, 'order_detail.html', {'order': order, 'order_items': order_items})


def search(request):
    products = Product.objects.filter(name__contains=request.GET['title'])
    return render(request, 'home.html', {'products': products})


def sendEmail(order_id):
    transaction = Order.objects.get(id=order_id)
    order_items = OrderItem.objects.filter(order=transaction)

    try:
        subject = "ZStore - New Order #{}".format(transaction.id)
        to = ['{}'.format(transaction.emailAddress)]
        from_email = "orders@zero2launch.com"
        order_information = {
            'transaction': transaction,
            'order_items': order_items
        }
        message = get_template('email/email.html').render(order_information)
        msg = EmailMessage(subject, message, to=to, from_email=from_email)
        msg.content_subtype = 'html'
        msg.send()
    except IOError as e:
        return e

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data.get('subject')
            from_email = form.cleaned_data.get('from_email')
            message = form.cleaned_data.get('message')
            name = form.cleaned_data.get('name')

            message_format = "{0} has sent you a new message:\n\n{1}".format(name, message)

            msg = EmailMessage(
                subject,
                message_format,
                to=['contact@zero2launch.io'],
                from_email=from_email
            )

            msg.send()

            return render(request, 'contact_success.html')


    else:
        form = ContactForm()

    return render(request, 'contact.html', {'form': form})
