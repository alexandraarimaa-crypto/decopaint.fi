# pk_paytrail/views.py

from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from pk_paytrail.hmac_calculator import Item, Customer, DeliveryAddress, RedirectUrls, Body, Crypto
from order.models import Order, OrderItem
from shop.models import Variant, Product
from django.conf import settings
from django.http import JsonResponse
from mail.views import send_email_to_admin, send_message
from decimal import Decimal
from cart.cart import Cart
import urllib.request
from urllib.parse import unquote
import json
import datetime
import uuid
from django.shortcuts import render
import requests
from shop.models import Product
from shop.analytics import (
    build_google_ads_enhanced_conversion_data,
    build_google_customer_reviews_data,
    build_purchase_event,
)
from decimal import InvalidOperation
from django.urls import reverse
from django_q.tasks import async_task
from django.db import transaction
import hmac
import logging


logger = logging.getLogger(__name__)

def generate_nonce():
    """Generate unique nonce for Paytrail API request"""
    return str(uuid.uuid4())

def generate_timestamp():
    """Generate current timestamp for Paytrail API request"""
    return datetime.datetime.utcnow().isoformat()

def debug_log(message, data=None):
    """
    Log only a short checkpoint name when explicitly enabled.

    Existing callers sometimes pass customer fields, request payloads, HMAC
    values, or provider responses. Never write those values to application
    logs.
    """
    if not getattr(settings, "PAYMENT_DEBUG_LOGGING", False):
        return

    checkpoint = str(message).split(":", 1)[0][:100]
    logger.debug("Paytrail checkpoint: %s", checkpoint)


def _has_ad_user_data_consent(request):
    if request.COOKIES.get("cookie_consent") != "granted":
        return False

    try:
        consent = json.loads(unquote(request.COOKIES.get("cookie_settings", "")))
    except (TypeError, ValueError, json.JSONDecodeError):
        return False
    return consent.get("ad_user_data") == "granted"


def _checkout_params(request):
    """Return every signed Paytrail query parameter in deterministic order."""
    return dict(sorted(
        (key, value)
        for key, value in request.GET.items()
        if key.startswith("checkout-")
    ))


def _has_valid_paytrail_signature(request):
    signature = request.GET.get("signature", "")
    if not signature:
        return False

    if request.GET.get("checkout-algorithm") != "sha256":
        return False

    expected_signature = Crypto.calculate_hmac(
        Crypto,
        settings.PK_PAYTRAIL_MERCHANT_SECRET,
        _checkout_params(request),
    )
    return hmac.compare_digest(signature, expected_signature)


def _expected_amount_cents(order):
    return int(
        (order.total_price * Decimal("100")).quantize(Decimal("1"))
    )


def _queue_order_confirmation(request, order):
    full_order_detail_url = request.build_absolute_uri(
        reverse("user:order_details", args=[order.id])
    )
    language_code = getattr(request, "LANGUAGE_CODE", settings.LANGUAGE_CODE)
    transaction.on_commit(
        lambda: async_task(
            "shop.tasks.send_order_confirmation_email",
            order.id,
            full_order_detail_url,
            language_code,
        )
    )


def _queue_order_merchant_sync(order):
    """
    Queue an upsert-only Merchant refresh after a confirmed order commits.

    Only the products in the order are refreshed. The task never runs the
    full-catalog deletion workflow.
    """
    if not getattr(settings, "MERCHANT_SYNC_ENABLED", True):
        return False

    order_id = order.id
    transaction.on_commit(
        lambda: async_task(
            "google_shopping.tasks.sync_order_products",
            order_id,
        )
    )
    return True


# pk_paytrail/views.py
def create_order_from_verified_data(request, current_user, user_data, cart, base_url):
    """
    Create order from verified cart data with prices from database
    Preserves all variant data for historical records
    """
    debug_log("=== CREATING ORDER FROM VERIFIED DATA ===")
    
    try:
        # Get verified order data with prices from database
        verified_data = cart.create_verified_order_data()
        
        if not verified_data['items']:
            raise Exception("Ostoskori on tyhjä tai sisältää virheellisiä tuotteita")
        
        # Create the order
        order = Order()
        
        # Set user if authenticated
        if current_user.is_authenticated:
            order.user = current_user
        
        # Set customer information
        order.email = user_data['email']
        order.company = user_data['company']
        order.vat = user_data['vat']
        order.first_name = user_data['first_name']
        order.last_name = user_data['last_name']
        order.address = user_data['address']
        order.postal = user_data['postal']
        order.city = user_data['city']
        order.phone = user_data['phone']
        
        # Set billing address if different from shipping
        if user_data.get('bill_address'):
            order.bill_address = user_data['bill_address']
            order.bill_postal = user_data['bill_postal']
            order.bill_city = user_data['bill_city']
        else:
            # Same as shipping address
            order.bill_address = user_data['address']
            order.bill_postal = user_data['postal']
            order.bill_city = user_data['city']
        
        # Set shipping method from cart
        order.shipping_method = cart.selected_shipping_method
        debug_log(f"Asetetaan toimitustapa: {cart.selected_shipping_method}")
        
        # Use verified prices from database
        order.subtotal_price = verified_data['subtotal_after_coupon']
        order.delivery_price = verified_data['shipping_price']
        order.total_price = verified_data['total_price']
        
        debug_log("=== VERIFIED ORDER PRICES FROM DATABASE ===")
        debug_log(f"Tuotteiden välisumma: {verified_data['subtotal_before_coupon']}€")
        debug_log(f"Kupongin alennus: {verified_data.get('discount_amount', 0)}% + {verified_data.get('amount_discount', 0)}€")
        debug_log(f"Välisumma kupongin jälkeen: {verified_data['subtotal_after_coupon']}€")
        debug_log(f"Toimitusmaksu: {verified_data['shipping_price']}€")
        debug_log(f"Loppusumma: {verified_data['total_price']}€")
        
        # Set initial status
        order.status = 'pending'
        order.payed = False
        
        # Save the order first to get an ID
        order.save()
        debug_log(f"Tallennettu tilaus ID: {order.id}")
        
        # Create order items from verified data - preserve ALL variant data
        for item_data in verified_data['items']:
            order_item = OrderItem()
            order_item.order = order
            order_item.product = item_data['product']
            order_item.variant = item_data['variant']
            order_item.quantity = item_data['quantity']
            order_item.price = item_data['total_price']  # Total price for the quantity
            
            # Store ALL variant parameters from the product/variant for historical preservation
            if item_data['variant']:
                variant = item_data['variant']
                # Store basic variant attributes
                order_item.color = variant.get_color_name()
                order_item.size = variant.size
                order_item.grain = variant.grain
                order_item.gloss = variant.gloss
                order_item.weight = variant.weight if variant.weight else Decimal('0')
                order_item.barcode = variant.barcode
                
                # Store complete color display data for historical preservation
                color_data = variant.get_active_color()
                order_item.color_type = color_data.get('type', '')
                if color_data.get('type') == 'color2' and color_data.get('rgb'):
                    order_item.r = color_data['rgb'][0]
                    order_item.g = color_data['rgb'][1]
                    order_item.b = color_data['rgb'][2]
                order_item.thumbnail_url = variant.get_thumbnail_url()
            else:
                # For products without variants, store basic product info
                product = item_data['product']
                order_item.color = ''
                order_item.size = ''
                order_item.grain = ''
                order_item.gloss = ''
                order_item.weight = Decimal('0')
                order_item.barcode = product.barcode
                order_item.thumbnail_url = product.thumbnail.url if product.thumbnail else ''
                order_item.color_type = ''
                order_item.r = None
                order_item.g = None
                order_item.b = None
            
            order_item.save()
            debug_log(f"Lisätty tilauskohde: {item_data['product'].name}, Määrä: {item_data['quantity']}, Hinta: {item_data['total_price']}€")
        
        # Apply coupon if exists
        if verified_data['coupon']:
            order.coupon = verified_data['coupon']
            order.save()
            debug_log(f"Käytetty kuponkia: {verified_data['coupon'].code}")
        
        # Refresh the order from database to ensure we have latest values
        order.refresh_from_db()
        debug_log("=== LOPULLISET TILAUKSEN HINNAT TALLENNUKSEN JÄLKEEN ===")
        debug_log(f"Tilauksen välisumma: {order.subtotal_price}€")
        debug_log(f"Tilauksen toimitusmaksu: {order.delivery_price}€")
        debug_log(f"Tilauksen loppusumma: {order.total_price}€")
        
        return order
        
    except Exception as e:
        debug_log(f"Virhe tilauksen luonnissa: {str(e)}")
        import traceback
        traceback.print_exc()
        raise e

@require_POST
def create_payment(request):
    """
    Main payment creation endpoint with verified prices
    """
    debug_log("=== PAYMENT CREATION WITH VERIFIED PRICES STARTED ===")
    
    if request.method == 'POST':
        current_user = request.user
        
        # Log received form data
        debug_log("Received form data:")
        for key, value in request.POST.items():
            debug_log(f"  {key}: {value}")
        
        # Retrieve form data from the request
        email = request.POST.get('email')
        company = request.POST.get('company')
        vat = request.POST.get('vat')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        postal = request.POST.get('postal')
        city = request.POST.get('city')
        phone = request.POST.get('phone')
        bill_address = request.POST.get('bill_address')
        bill_postal = request.POST.get('bill_postal')
        bill_city = request.POST.get('bill_city')
        payment_method = request.POST.get('payment_method', 'online')
        selected_bank = request.POST.get('selected_bank')
        bank_id = request.POST.get('bank_id')

        debug_log(f"Payment method: {payment_method}")
        debug_log(f"Selected bank: {selected_bank}")
        debug_log(f"Bank ID: {bank_id}")

        # Create a dictionary with the form data
        user_data = {
            'email': email,
            'company': company,
            'vat': vat,
            'first_name': first_name,
            'last_name': last_name,
            'address': address,
            'postal': postal,
            'city': city,
            'phone': phone,
            'bill_address': bill_address,
            'bill_postal': bill_postal,
            'bill_city': bill_city,
        }

        cart = Cart(request)
        
        # Validate that cart is not empty
        if len(cart) == 0:
            debug_log("Cart is empty")
            return JsonResponse({
                'success': False,
                'error': 'Ostoskorisi on tyhjä'
            })

        # IMPORTANT: Prices are automatically updated when Cart is initialized
        # In the simplified version, update_all_prices_from_database() is called in __init__
        debug_log("=== AUTOMATIC PRICE UPDATE FROM DATABASE ===")
        debug_log("Cart prices automatically updated during initialization")
        
        # Log current cart shipping method and verified prices
        debug_log(f"Current cart shipping method: {cart.selected_shipping_method}")
        debug_log(f"Cart subtotal: {cart.get_subtotal_price()}")
        debug_log(f"Cart shipping price: {cart.get_delivery_price()}")
        debug_log(f"Cart total price: {cart.get_total_price()}")

        base_url = request.build_absolute_uri('/')
        debug_log(f"Base URL: {base_url}")

        # Check payment method and route accordingly
        if payment_method == 'cod':
            if cart.selected_shipping_method != 'pickup':
                return JsonResponse({
                    'success': False,
                    'error': 'Maksutapa "Maksaa noudettaessa" on sallittu vain noudon kanssa.'
                })
            debug_log("Processing cash on delivery payment with verified prices")
            return handle_cash_on_delivery(request, current_user, user_data, cart, base_url)
        else:
            debug_log("Processing online payment with selected bank and verified prices")
            return handle_online_payment_with_bank(request, current_user, user_data, cart, base_url, selected_bank, bank_id)

def handle_online_payment_with_bank(request, current_user, user_data, cart, base_url, selected_bank, bank_id):
    """
    Handle online payment with pre-selected bank using verified prices
    """
    debug_log("=== ONLINE PAYMENT WITH VERIFIED PRICES STARTED ===")
    debug_log(f"Selected bank: {selected_bank}, Bank ID: {bank_id}")
    
    try:
        # Create order with verified prices from database
        debug_log("Creating order with verified prices...")
        new_order = create_order_from_verified_data(request, current_user, user_data, cart, base_url)
        debug_log(f"Order created with ID: {new_order.id}")
        
        # Verify order has correct prices
        debug_log(f"Order shipping method: {new_order.shipping_method}")
        debug_log(f"Order delivery price: {new_order.delivery_price}")
        debug_log(f"Order subtotal price: {new_order.subtotal_price}")
        debug_log(f"Order total price: {new_order.total_price}")
        
        # Double-check: verify prices match cart
        cart_total = cart.get_total_price()
        order_total = new_order.total_price
        if abs(cart_total - order_total) > Decimal('0.01'):
            debug_log(f"PRICE MISMATCH DETECTED: Cart total {cart_total} vs Order total {order_total}")
            # Update order with correct price
            new_order.total_price = cart_total
            new_order.save()
            debug_log(f"Order total price corrected to: {cart_total}")
        
        # Mark order as online payment
        try:
            new_order.payment_method = 'online'
            new_order.save()
            debug_log("Order marked as online payment")
        except Exception as e:
            debug_log(f"payment_method field not available: {e}")
            new_order.save()

        # Create payment with selected bank using verified order data
        debug_log("Creating payment in Paytrail with verified prices...")
        payment_data = create_payment_for_order(request, user_data, new_order)
        
        # Check if payment creation was successful
        if payment_data.get('error'):
            debug_log(f"Payment creation failed: {payment_data['error']}")
            return JsonResponse({
                'success': False,
                'error': payment_data['error']
            })
        
        debug_log("Payment created successfully in Paytrail")
        debug_log(f"Available banks in response: {len(payment_data.get('banks', []))}")
        
        # Find the selected bank URL and parameters from the payment data
        selected_bank_url = None
        selected_bank_parameters = []
        
        if payment_data.get('banks'):
            for bank in payment_data['banks']:
                debug_log(f"Checking bank: {bank.get('name')} vs selected: {selected_bank}")
                if bank.get('name') == selected_bank:
                    selected_bank_url = bank.get('url')
                    selected_bank_parameters = bank.get('parameters', [])
                    debug_log(f"Found matching bank URL: {selected_bank_url}")
                    debug_log(f"Bank parameters: {len(selected_bank_parameters)} parameters")
                    break
        
        if not selected_bank_url:
            debug_log(f"Selected bank '{selected_bank}' not found in available banks")
            return JsonResponse({
                'success': False,
                'error': 'Valittua maksutapaa ei löytynyt. Yritä uudelleen valitsemalla toinen maksutapa.'
            })
        
        debug_log("Cart preserved for payment processing - will be cleared after successful payment")
        
        return JsonResponse({
            'success': True,
            'redirect_url': selected_bank_url,
            'parameters': selected_bank_parameters,
            'order_id': new_order.id
        })
        
    except Exception as e:
        debug_log(f"Online payment creation error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': 'Maksun luonnissa tapahtui virhe. Ota yhteyttä asiakaspalveluun.'
        })

def create_payment_for_order(request, user_data, order):
    """
    Create payment for order in Paytrail system using verified order data
    """
    debug_log("=== CREATING PAYMENT IN PAYTRAIL WITH VERIFIED PRICES ===")
    debug_log(f"Order ID: {order.id}")
    debug_log(f"Order total price: {order.total_price}€")
    
    try:
        # Extract user data for Paytrail API
        first_name = user_data['first_name']
        last_name = user_data['last_name']
        email = user_data['email']
        phone = user_data['phone']
        vat = user_data['vat']
        company = user_data['company']
        street = user_data['address']
        postal = user_data['postal']
        city = user_data['city']
        country = "FI"

        debug_log(f"Customer: {first_name} {last_name}, Email: {email}")

        # Paytrail API configuration
        api_url = settings.PK_PAYTRAIL_API_URL
        redirectUrls = RedirectUrls(
            settings.PK_PAYTRAIL_REDIRECT_SUCCESS_URL, 
            settings.PK_PAYTRAIL_REDIRECT_CANCEL_URL
        )
        merchant_id = settings.PK_PAYTRAIL_MERCHANT_ID
        merchant_secret = settings.PK_PAYTRAIL_MERCHANT_SECRET
        currency = settings.PK_PAYTRAIL_CURRENCY
        language = settings.PK_PAYTRAIL_LANGUAGE
        
        debug_log(f"API URL: {api_url}")
        debug_log(f"Merchant ID: {merchant_id}")
        
        # Order details for Paytrail - Use the verified order total price
        stamp = str(order.id)
        customer = Customer(email, first_name, last_name, phone, vat, company)
        deliveryAddress = DeliveryAddress(street, postal, city, country)
        
        # Use verified total price from order (calculated from database prices)
        total_price = order.total_price
        total_price_cents = int(total_price * 100)
        
        debug_log("=== VERIFIED PAYMENT AMOUNT ===")
        debug_log(f"Total price from verified order: {total_price}€ ({total_price_cents} cents)")
        
        # Prepare headers for Paytrail API request
        headers = {
            "checkout-account": merchant_id,
            "checkout-algorithm": "sha256",
            "checkout-method": "POST",
            "checkout-nonce": generate_nonce(),
            "checkout-timestamp": generate_timestamp(),
            'Content-Type': 'application/json; charset=utf-8',
        }
        sorted_headers = dict(sorted(headers.items()))

        debug_log("Request headers prepared")

        # Create request body
        b = Body(stamp, merchant_id, total_price_cents, currency, language, customer, deliveryAddress, redirectUrls)
        body_dict = b.toDictionary()
        body = json.dumps(body_dict, separators=(',', ':'))

        debug_log("Request body prepared with verified prices")

        # Calculate HMAC signature for security
        signature = Crypto.calculate_hmac(Crypto, merchant_secret, sorted_headers, body)
        headers['signature'] = signature
        
        debug_log(f"HMAC signature calculated: {signature[:20]}...")

        # Make the request to Paytrail API
        debug_log(f"Sending request to Paytrail API: {api_url}")
        paytrail_request = urllib.request.Request(
            api_url,
            body.encode('utf-8'),
            headers=headers
        )

        # Perform the request and get response
        debug_log("Making request to Paytrail...")
        with urllib.request.urlopen(paytrail_request) as response:
            response_content = response.read()
            response_text = response_content.decode('utf-8')

            debug_log("Paytrail API response received")

            # Parse JSON response
            response_data = json.loads(response_text)
            
            debug_log("Paytrail API response parsed successfully")
            debug_log(f"Transaction ID: {response_data.get('transactionId')}")

            # Add transaction id to the order
            order.transaction_id = response_data.get("transactionId")
            order.save()
            debug_log(f"Transaction ID saved to order: {order.transaction_id}")

            terms = response_data.get("terms")

            # Extract providers data and additional parameters
            banks = []
            for provider in response_data.get("providers", []):
                bank = {
                    "name": provider.get("name", ""),
                    "url": provider.get("url", ""),
                    "icon": provider.get("icon", ""),
                    "svg": provider.get("svg", ""),
                    "parameters": []
                }

                # Extract additional parameters if available
                parameters = provider.get("parameters", [])
                for parameter in parameters:
                    param_data = {
                        "name": parameter.get("name", ""),
                        "value": parameter.get("value", "")
                    }
                    bank["parameters"].append(param_data)

                banks.append(bank)
                
                debug_log(f"Provider: {bank['name']}")

            debug_log(f"Total banks extracted: {len(banks)}")
            
            return {
                'order': order.id, 
                'banks': banks, 
                'terms': terms
            }
        
    except urllib.error.HTTPError as e:
        error_content = e.read().decode('utf-8')
        debug_log(f"HTTP Error {e.code}: {e.reason}")
        debug_log(f"Response Body: {error_content}")
            
        return {
            'error': f"Paytrail API virhe {e.code}: {e.reason}. Ota yhteyttä asiakaspalveluun."
        }
        
    except urllib.error.URLError as e:
        debug_log(f"URL Error: {e.reason}")
        return {
            'error': f"Yhteysvirhe Paytrail-palveluun: {e.reason}. Tarkista internetyhteys ja yritä uudelleen."
        }
        
    except Exception as e:
        debug_log(f"Unexpected error creating payment: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'error': f"Odottamaton virhe maksun luonnissa: {str(e)}. Ota yhteyttä asiakaspalveluun."
        }

def handle_cash_on_delivery(request, current_user, user_data, cart, base_url):
    """
    Handle cash on delivery payment with verified prices
    """
    debug_log("=== CASH ON DELIVERY WITH VERIFIED PRICES ===")
    
    try:
        # Create order with verified prices
        debug_log("Creating order for cash on delivery with verified prices...")
        new_order = create_order_from_verified_data(request, current_user, user_data, cart, base_url)
        debug_log(f"Order created with ID: {new_order.id}")
        
        # Double-check: verify prices match cart
        cart_total = cart.get_total_price()
        order_total = new_order.total_price
        if abs(cart_total - order_total) > Decimal('0.01'):
            debug_log(f"PRICE MISMATCH DETECTED: Cart total {cart_total} vs Order total {order_total}")
            # Update order with correct price
            new_order.total_price = cart_total
            new_order.save()
            debug_log(f"Order total price corrected to: {cart_total}")
        
        # Mark order as cash on delivery and not paid
        new_order.payed = False
        try:
            new_order.payment_method = 'cod'
            debug_log("Order marked as cash on delivery")
        except Exception as e:
            debug_log(f"payment_method field not available: {e}")
        
        new_order.status = 'processing'
        new_order.notes = "Maksutapa: Maksaa noudettaessa"
        new_order.save()
        _queue_order_merchant_sync(new_order)

        # The confirmation page may be opened only from this checkout session.
        # The pending flag also makes the confirmation email idempotent.
        request.session["last_order_id"] = new_order.id
        request.session["cod_confirmation_pending"] = new_order.id

        # Clear the cart - for COD we can clear immediately since no payment processing
        cart.clear()
        debug_log("Cart cleared successfully for COD order")
        
        # Return success with order ID
        return JsonResponse({
            'success': True,
            'order_id': new_order.id,
            'payment_method': 'cod'
        })
        
    except Exception as e:
        debug_log(f"Cash on delivery order creation error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': 'Tilauksen luonnissa tapahtui virhe. Ota yhteyttä asiakaspalveluun.'
        }, status=500)


@csrf_exempt
def payment_success(request):
    """
    Handle a signed Paytrail success callback or a session-owned COD return.

    Paytrail may call the URL multiple times. The paid transition and
    confirmation side effects therefore have to be idempotent.
    """
    checkout_account = request.GET.get('checkout-account')
    checkout_stamp = request.GET.get('checkout-stamp')
    direct_order_id = request.GET.get('order_id')
    payment_method = request.GET.get('payment_method', 'online')
    order = None
    should_queue_confirmation = False

    if checkout_account and checkout_stamp:
        if not _has_valid_paytrail_signature(request):
            return HttpResponseForbidden("Virheellinen allekirjoitus.")

        if checkout_account != str(settings.PK_PAYTRAIL_MERCHANT_ID):
            return HttpResponseForbidden("Virheellinen kauppiastunnus.")

        checkout_status = request.GET.get("checkout-status")
        if checkout_status not in {"ok", "pending", "delayed"}:
            return HttpResponseForbidden("Maksua ei ole vahvistettu.")

        try:
            order_id = int(checkout_stamp)
            received_amount = int(request.GET.get("checkout-amount", ""))
        except (TypeError, ValueError):
            return HttpResponseForbidden("Virheelliset maksutiedot.")

        received_transaction_id = request.GET.get("checkout-transaction-id", "")
        if not received_transaction_id:
            return HttpResponseForbidden("Maksutapahtuma puuttuu.")

        with transaction.atomic():
            try:
                order = Order.objects.select_for_update().get(id=order_id)
            except Order.DoesNotExist:
                return HttpResponseForbidden("Tilausta ei löytynyt.")

            if received_amount != _expected_amount_cents(order):
                return HttpResponseForbidden("Maksun summa ei vastaa tilausta.")

            if order.transaction_id and not hmac.compare_digest(
                order.transaction_id,
                received_transaction_id,
            ):
                return HttpResponseForbidden("Maksutapahtuma ei vastaa tilausta.")

            duplicate_transaction = (
                Order.objects
                .exclude(id=order.id)
                .filter(transaction_id=received_transaction_id, payed=True)
                .exists()
            )
            if duplicate_transaction:
                return HttpResponseForbidden("Maksutapahtuma on jo käytetty.")

            if checkout_status in {"pending", "delayed"}:
                return render(request, "order/pending.html", {
                    "order_id": order.id,
                }, status=202)

            if not order.payed:
                order.payed = True
                order.status = "processing"
                order.transaction_id = received_transaction_id
                order.save(update_fields=[
                    "payed",
                    "status",
                    "transaction_id",
                    "updated",
                ])
                should_queue_confirmation = True

        Cart(request).clear()
        request.session["last_order_id"] = order.id

    elif direct_order_id and payment_method == 'cod':
        try:
            order = Order.objects.get(id=int(direct_order_id))
        except (Order.DoesNotExist, TypeError, ValueError):
            return HttpResponseForbidden("Tilausta ei löytynyt.")

        session_owns_order = request.session.get("last_order_id") == order.id
        user_owns_order = (
            request.user.is_authenticated
            and order.user_id == request.user.id
        )

        if (
            order.payment_method != "cod"
            or not (session_owns_order or user_owns_order)
        ):
            return HttpResponseForbidden("Tilaus ei kuulu tähän istuntoon.")

        should_queue_confirmation = (
            request.session.pop("cod_confirmation_pending", None) == order.id
        )
    else:
        return HttpResponseForbidden("Maksuvahvistus puuttuu.")

    if should_queue_confirmation:
        _queue_order_confirmation(request, order)
        if order.payment_method == "online":
            _queue_order_merchant_sync(order)

    purchase_session_key = f"ga4_purchase_rendered_{order.id}"
    customer_reviews_session_key = f"google_customer_reviews_rendered_{order.id}"
    purchase_event = None
    google_ads_enhanced_conversion = None
    google_customer_reviews = None
    if not request.session.get(purchase_session_key):
        purchase_event = build_purchase_event(order)
        if _has_ad_user_data_consent(request):
            google_ads_enhanced_conversion = (
                build_google_ads_enhanced_conversion_data(order)
            )
        request.session[purchase_session_key] = True

    # Google Customer Reviews renders its own opt-in after a real order.  Keep
    # it separate from advertising consent and show it at most once per order.
    if not request.session.get(customer_reviews_session_key):
        google_customer_reviews = build_google_customer_reviews_data(order)
        if google_customer_reviews:
            request.session[customer_reviews_session_key] = True

    return render(request, "order/created.html", {
        "order_id": order.id,
        "payment_method": order.payment_method,
        "status": request.GET.get('checkout-status', 'success'),
        "ga4_event": purchase_event,
        "google_ads_enhanced_conversion": google_ads_enhanced_conversion,
        "google_customer_reviews": google_customer_reviews,
    })


@csrf_exempt
def payment_cancel(request):
    """
    Handle a signed and idempotent Paytrail cancellation.
    """
    if not _has_valid_paytrail_signature(request):
        return HttpResponseForbidden("Virheellinen allekirjoitus.")

    if request.GET.get("checkout-account") != str(settings.PK_PAYTRAIL_MERCHANT_ID):
        return HttpResponseForbidden("Virheellinen kauppiastunnus.")

    if request.GET.get("checkout-status") != "fail":
        return HttpResponseForbidden("Virheellinen peruutuksen tila.")

    try:
        order_id = int(request.GET.get("checkout-stamp", ""))
        received_amount = int(request.GET.get("checkout-amount", ""))
    except (TypeError, ValueError):
        return HttpResponseForbidden("Virheelliset maksutiedot.")

    received_transaction_id = request.GET.get("checkout-transaction-id", "")
    if not received_transaction_id:
        return HttpResponseForbidden("Maksutapahtuma puuttuu.")

    with transaction.atomic():
        try:
            order = Order.objects.select_for_update().get(id=order_id)
        except Order.DoesNotExist:
            return HttpResponseForbidden("Tilausta ei löytynyt.")

        if received_amount != _expected_amount_cents(order):
            return HttpResponseForbidden("Maksun summa ei vastaa tilausta.")

        if order.transaction_id and not hmac.compare_digest(
            order.transaction_id,
            received_transaction_id,
        ):
            return HttpResponseForbidden("Maksutapahtuma ei vastaa tilausta.")

        if order.payed:
            return HttpResponseForbidden("Maksettua tilausta ei voi peruuttaa.")

        if order.status != "canceled":
            order.payed = False
            order.status = "canceled"
            order.transaction_id = received_transaction_id
            order.save(update_fields=[
                "payed",
                "status",
                "transaction_id",
                "updated",
            ])

    return render(request, 'order/cancelled.html', {})

def get_payment_methods(request):
    """
    Get available payment methods from Paytrail for display in checkout
    """
    debug_log("=== GET PAYMENT METHODS ===")
    
    try:
        banks = get_available_banks()
        debug_log(f"Retrieved {len(banks)} payment methods")
        return JsonResponse({
            'success': True,
            'banks': banks
        })
    except Exception as e:
        debug_log(f"Error getting payment methods: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': 'Maksutapojen lataus epäonnistui. Yritä myöhemmin uudelleen.'
        })

def get_available_banks():
    """
    Get list of available banks and payment methods from Paytrail
    """
    debug_log("=== GET AVAILABLE BANKS FROM PAYTRAIL ===")
    
    try:
        url = 'https://services.paytrail.com/merchants/payment-providers'
        merchant_id = settings.PK_PAYTRAIL_MERCHANT_ID
        merchant_secret = settings.PK_PAYTRAIL_MERCHANT_SECRET

        debug_log(f"Requesting payment providers from: {url}")
        debug_log(f"Merchant ID: {merchant_id}")

        # Prepare headers for Paytrail API request
        headers = {
            "checkout-account": merchant_id,
            "checkout-algorithm": "sha256",
            "checkout-method": "GET",
            "checkout-nonce": generate_nonce(),
            "checkout-timestamp": generate_timestamp(),
            'Content-Type': 'application/json; charset=utf-8',
        }
        sorted_headers = dict(sorted(headers.items()))

        # Calculate HMAC signature
        signature = Crypto.calculate_hmac(Crypto, merchant_secret, sorted_headers)
        headers['signature'] = signature
        
        debug_log(f"HMAC signature calculated: {signature[:20]}...")

        # Make request to Paytrail API
        debug_log("Making request to Paytrail payment providers API...")
        paytrail_request = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(paytrail_request) as response:
            response_data = response.read().decode('utf-8')
            data = json.loads(response_data)

            debug_log(f"Received {len(data)} payment providers from Paytrail")

            banks = []
            for provider in data:
                # Filter relevant payment methods (banks, mobile payments, credit cards)
                if provider.get('group') in ['bank', 'mobile', 'creditcard']:
                    bank = {
                        "name": provider.get("name", ""),
                        "url": provider.get("url", ""),
                        "icon": provider.get("icon", ""),
                        "svg": provider.get("svg", ""),
                        "group": provider.get("group", ""),
                        "id": provider.get("id", ""),
                        "parameters": provider.get("parameters", [])
                    }
                    banks.append(bank)
                    debug_log(f"Added provider: {bank['name']} (group: {bank['group']})")

            debug_log(f"Total filtered providers: {len(banks)}")
            return banks

    except urllib.error.HTTPError as e:
        error_content = e.read().decode('utf-8')
        debug_log(f"HTTP Error getting banks: {e.code} - {e.reason}")
        debug_log(f"Error response: {error_content}")
        return []
    except urllib.error.URLError as e:
        debug_log(f"URL Error getting banks: {e.reason}")
        return []
    except Exception as e:
        debug_log(f"Error getting banks: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_payment_data(transaction_id):
    """
    Get payment data from Paytrail for a specific transaction
    Used for payment status verification
    """
    debug_log(f"=== GET PAYMENT DATA FOR TRANSACTION: {transaction_id} ===")
    
    url = f'https://services.paytrail.com/payments/{transaction_id}'
    
    merchant_id = settings.PK_PAYTRAIL_MERCHANT_ID
    merchant_secret = settings.PK_PAYTRAIL_MERCHANT_SECRET

    headers = {
        "checkout-account": merchant_id,
        "checkout-method": "GET",
        "checkout-algorithm": "sha256",
        "checkout-timestamp": generate_timestamp(),
        "checkout-nonce": generate_nonce(),
        "checkout-transaction-id": transaction_id,
    }
    sorted_headers = dict(sorted(headers.items()))

    signature = Crypto.calculate_hmac(Crypto, merchant_secret, sorted_headers)
    headers["signature"] = signature

    try:
        debug_log(f"Requesting payment data from: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        debug_log("Payment data retrieved successfully")
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        debug_log(f"HTTP error occurred: {http_err}")
    except requests.exceptions.RequestException as req_err:
        debug_log(f"Request error occurred: {req_err}")
    except Exception as exc:
        debug_log(f"An unexpected error occurred: {exc}")

    return None
