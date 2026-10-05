from django.shortcuts import render, redirect
from django.contrib.auth import login
from users.forms import CustomUserChangeForm, CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from pk_paytrail.views import get_payment_data
from order.models import Order
from order.forms import OrderUpdateForm
from cart.cart import Cart
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.contrib.auth.models import Group
from django.template.loader import render_to_string
from users.models import CustomUser
from django.forms.utils import ErrorDict
import pytz
from datetime import datetime, timedelta
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from mail.views import send_message
from shop.models import Product, RecentProductView

class ChangePasswordView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'profile/change_password.html'
    success_message = "Salasana vaihdettu onnistuneesti!"
    success_url = reverse_lazy('user:profile')

def save_product_views_from_session_to_db(user, session):
    recent_views = session.get('recent_views', [])

    for product_id in recent_views:
        product = Product.objects.get(id=product_id)
        if not RecentProductView.objects.filter(user=user, product=product).exists():
            RecentProductView.objects.create(user=user, product=product)

    session.pop('recent_views', None)

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)

            # Сохранение просмотров из сессии в базу данных
            save_product_views_from_session_to_db(user, request.session)

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # This is an AJAX request, return JSON response
                return JsonResponse({'success': True})
            else:
                # This is a regular request, redirect the user
                return redirect('shop:main')  # Replace 'some-success-url' with the appropriate URL
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # This is an AJAX request, return JSON response with error
                return JsonResponse({'success': False, 'error': 'Väärä sähköpostiosoite tai salasana.'})
            else:
                # This is a regular request, return the form with error message
                error_message = 'Väärä sähköpostiosoite tai salasana.'
                return render(request, 'registration/login.html', {'error_message': error_message})
    else:
        # This is a GET request, return the login form
        return render(request, 'registration/login.html')

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def order_history(request):
    # Get the list of orders for the current user
    orders_list = request.user.orders.all()

    # Define the number of items per page
    items_per_page = 10

    # Create a Paginator object
    paginator = Paginator(orders_list, items_per_page)

    # Get the page number from the GET parameter
    page_number = request.GET.get('page')

    try:
        # Get the page object
        orders = paginator.page(page_number)
    except PageNotAnInteger:
        # If page number is not an integer, show the first page
        orders = paginator.page(1)
    except EmptyPage:
        # If page number is out of range, show the last page
        orders = paginator.page(paginator.num_pages)

    return render(request, 'profile/order_history.html', {'orders': orders})

@login_required
def load_payment_details(request, order_id):
    """
    Load payment details only for the order owner or a superuser.
    """
    if request.user.is_superuser:
        order = get_object_or_404(Order, id=order_id)
    else:
        order = get_object_or_404(Order, id=order_id, user=request.user)

    transaction_id = order.transaction_id

    payment = get_payment_data(transaction_id)

    payed_time = ''
    payed_sum = ''
    if payment:
        timestamp_value = payment['createdAt']
        payed_time = datetime.fromisoformat(timestamp_value[:-1])
        payed_time += timedelta(hours=2)
        payed_sum = int(payment['amount'])/100

    html_response = render_to_string('profile/payment_details.html', { 
        'payment': payment, 
        'payed_time': payed_time, 
        'payed_sum': payed_sum,
        'order': order
    })
    return JsonResponse({'html': html_response})

@login_required
def order_details(request, pk):
    """
    Display order details with POS-style design
    """
    order = get_object_or_404(Order, id=pk, user=request.user)
    items = order.items.all()

    if request.method == 'POST':
        if 'renew_order' in request.POST:
            cart = Cart(request)
            for item in items:
                cart.add(
                    product=item.variant.product,
                    variant=item.variant,
                    quantity=int(item.quantity),
                    update_quantity=False,
                )
            messages.success(request, 'Tuotteet lisätty ostoskoriin.')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            
        if 'save_notes' in request.POST:
            notes = request.POST.get('notes', '').strip()
            order.notes = notes
            order.save()
            messages.success(request, 'Muistiinpanot tallennettu.')

    return render(request, 'profile/order_details.html', {
        'order': order, 
        'items': items
    })

@login_required
def profile(request):
    if request.method == 'POST':
        user_form = CustomUserChangeForm(request.POST, instance=request.user)

        if user_form.is_valid():
            user_form.save()
            # Add a success message
            messages.success(request, 'Profiilisi on päivitetty onnistuneesti.')
            return redirect('user:profile')
        else:
            # If the form is invalid, add an error message
            messages.error(request, 'Lomake sisältää virheitä. Korjaa ne ja yritä uudelleen.')
    else:
        user_form = CustomUserChangeForm(instance=request.user)

    return render(request, 'profile/profile.html', {'user_form': user_form})


def register(request):
    if request.method == 'POST':
        # Get user input from the registration form
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Check if user with the same email already exists
        if CustomUser.objects.filter(email=email).exists():
            # If user with the same email exists, return JSON response with error
            return JsonResponse({'success': False, 'error': "Käyttäjä samalla sähköpostiosoitteella on jo olemassa."})

        # Create a form instance with the POST data
        form = CustomUserCreationForm(request.POST)

        # Check if the form data is valid
        if form.is_valid():
            # If valid, create a new user object but do not save it yet
            new_user = form.save(commit=False)
            # Set the user's email
            new_user.email = email
            # Set the user's password
            new_user.set_password(password1)
            # Save the new user object to the database
            new_user.save()

            # Add the user to the "Asiakas" group
            asiakas_group = Group.objects.get(name='Asiakas')
            new_user.groups.add(asiakas_group)

            # Log in the newly registered user
            login(request, new_user)

            # Check if the request is an AJAX request
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                # If AJAX request, return JSON response indicating success
                return JsonResponse({'success': True})
            else:
                # If regular request, redirect the user to the main page
                return redirect('shop:main')
        else:
            # If form data is invalid, return JSON response with errors
            errors_dict = ErrorDict(form.errors)
            errors = {field: errors_dict.as_data()[field][0].message for field in errors_dict}
            return JsonResponse({'success': False, 'errors': errors})
    else:
        # If the request method is not POST, display a blank registration form
        form = CustomUserCreationForm()
        return render(request, 'registration/register.html', {'form': form})
    

@login_required
@require_POST
def send_register_email(request):
    """
    Send the welcome message only to the authenticated account.

    The previous implementation accepted an arbitrary email address from an
    unauthenticated request and could be abused as an email relay.
    """
    email = request.user.email
    subject = "Tervetuloa liittymään Deco Paint -verkkokauppaan!"
    context = {'email': email}
    send_message(email, subject, template_name='registration_email.html', context=context)

    return JsonResponse({'success': True})
