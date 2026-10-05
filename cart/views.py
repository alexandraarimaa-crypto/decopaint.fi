# cart/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from shop.models import Product, Variant, Coupon, Group, GroupSettings
from .cart import Cart
from .forms import CartAddProductForm, CouponForm
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib import messages
from shop.models import StoreSettings
from shop.analytics import build_cart_event, build_cart_params
import json
from decimal import Decimal

def debug_log(message, data=None):
    """Helper function for debug logging"""
    if data is not None:
        print(f"[DEBUG DATA] {data}")

@require_POST
def update_shipping_method(request):
    """
    Update selected shipping method in cart
    """
    try:
        data = json.loads(request.body)
        shipping_method = data.get('shipping_method')
        
        if shipping_method not in ['pickup', 'weight_based', 'postnord_lokero', 'postnord_kotiinkuljetus']:
            return JsonResponse({'success': False, 'error': 'Virheellinen toimitustapa'})
        
        cart = Cart(request)
        cart.set_shipping_method(shipping_method)
        
        # Get all calculated prices
        subtotal_price = cart.get_subtotal_price()
        delivery_price = cart.get_delivery_price()
        total_price = cart.get_total_price()
        total_tax = cart.get_total_tax()
        
        # Return updated cart information with all calculations
        return JsonResponse({
            'success': True,
            'subtotal_price': float(subtotal_price),
            'shipping_price': float(delivery_price),
            'total_price': float(total_price),
            'total_tax': float(total_tax),
            'selected_method': {
                'name': shipping_method,
                'price': float(delivery_price),
                'is_free': delivery_price == 0
            }
        })
        
    except Exception as e:
        debug_log(f"ERROR in update_shipping_method: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@require_POST
def cart_add(request, product_id):
    """Add product to cart"""
    if request.method == 'POST':
        form = CartAddProductForm(request.POST)

        if form.is_valid():
            cleaned_data = form.cleaned_data
            color = cleaned_data.get('color', '')
            size = cleaned_data.get('size', '')
            grain = cleaned_data.get('grain', '')
            gloss = cleaned_data.get('gloss', '')
            base = cleaned_data.get('base', '')
          
            cart = Cart(request)

            try:
                from django.db.models import Q
                
                query = Q(product=product_id, active=True)
                
                if color:
                    query &= (Q(color1=color) | Q(color2=color))
                else:
                    query &= (Q(color1='') | Q(color1__isnull=True)) & (Q(color2='') | Q(color2__isnull=True))
                    
                if size:
                    query &= Q(size=size)
                else:
                    query &= (Q(size='') | Q(size__isnull=True))
                    
                if grain:
                    query &= Q(grain=grain)
                else:
                    query &= (Q(grain='') | Q(grain__isnull=True))
                    
                if gloss:
                    query &= Q(gloss=gloss)
                else:
                    query &= (Q(gloss='') | Q(gloss__isnull=True))
                    
                if base:
                    query &= Q(base=base)
                else:
                    query &= (Q(base='') | Q(base__isnull=True))

                variant = Variant.objects.filter(query).first()
                
                if variant:
                    cart.add(
                        product=variant.product,
                        variant=variant,
                        quantity=cleaned_data['quantity'],
                        update_quantity=cleaned_data['update'],
                    )

                    messages.success(request, f"{variant.product.name} lisätty koriin.")

                    if cleaned_data['update']:
                        return JsonResponse({'status': 'päivitetty'})
                else:
                    messages.error(request, f"Tuotevaihtoehtoa ei löydy.")
                    
            except Exception as e:
                messages.error(request, f"Tapahtui virhe: {str(e)}")

        else:
            print(form.errors)

    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

def cart_remove(request, product_id, size_variant_id):
    """Remove product from cart"""
    cart = Cart(request)
    cart.remove_group(product_id, size_variant_id)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

def cart_remove_selected(request):
    """Remove selected items from cart"""
    if request.method == 'POST':
        selected_items = request.POST.getlist('selected_items')
        cart = Cart(request)
        
        for item_id in selected_items:
            try:
                product_id, variant_id = map(int, item_id.split('-'))
                cart.remove_group(product_id, variant_id)
            except (ValueError, Exception) as e:
                print(f"DEBUG: Error removing item {item_id}: {e}")
                continue
        
        return redirect('cart:checkout')
    else:
        return redirect('cart:checkout')
    
def cart_clear(request):
    """Clear entire cart"""
    cart = Cart(request)
    cart.clear()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

def cart_update(request):
    """Update cart quantities"""
    if request.method == 'POST':
        cart = Cart(request)
        product_ids = request.POST.getlist('product_id')
        variant_ids = request.POST.getlist('variant_id')
        quantities = request.POST.getlist('quantity')

        # Update the quantity for each product
        for product_id, variant_id, quantity in zip(product_ids, variant_ids, quantities):
            try:
                product = Product.objects.get(id=product_id)
                variant = Variant.objects.get(id=variant_id) if variant_id != '0' else None
                
                cart.add(
                    product=product,
                    variant=variant,
                    quantity=int(quantity),
                    update_quantity=True,
                )
            except (Product.DoesNotExist, Variant.DoesNotExist) as e:
                print(f"DEBUG: Error updating item: {e}")
                continue

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})

def cart_detail(request):
    """Display cart details"""
    cart = Cart(request)  # Prices are automatically updated in __init__
    
    applied_coupon = None

    if 'coupon_id' in request.session:
        try:
            coupon = Coupon.objects.get(id=request.session['coupon_id'])
            user_for_validation = request.user if request.user.is_authenticated else None
            if coupon.is_valid(user_for_validation):
                applied_coupon = coupon
            else:
                del request.session['coupon_id']
                messages.error(request, "Kuponki on vanhentunut tai ei ole voimassa.")
        except Coupon.DoesNotExist:
            applied_coupon = None
            if 'coupon_id' in request.session:
                del request.session['coupon_id']

    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            try:
                cart = Cart(request)
                coupon = Coupon.objects.get(code=code)
                min_purchase = coupon.min_purchase
                subtotal_price = cart.get_subtotal_price()
                
                user_for_validation = request.user if request.user.is_authenticated else None
                
                if coupon.is_valid(user_for_validation) and (min_purchase is None or subtotal_price >= min_purchase):
                    cart.apply_coupon_discount(request, coupon)
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
                else:
                    if coupon.single_use:
                        if coupon.used_by_anonymous:
                            messages.error(request, "Tämä kertakäyttökuponki on jo käytetty.")
                        elif request.user.is_authenticated and coupon.used_by.filter(id=request.user.id).exists():
                            messages.error(request, "Olet jo käyttänyt tämän kertakäyttökupongin.")
                        else:
                            messages.error(request, "Kuponki ei ole voimassa.")
                    elif min_purchase and subtotal_price < min_purchase:
                        messages.error(request, "Ostoskorin summa on liian pieni tämän kupongin käyttöön.")
                    else:
                        messages.error(request, "Kuponki ei ole voimassa.")
            except Coupon.DoesNotExist:
                messages.error(request, "Kuponkia ei löydy.")
    else:
        form = CouponForm()

    return render(request, 'cart/cart.html', {
        'cart': cart,
        'coupon_form': form,
        'coupon': applied_coupon,
    })


def remove_discount(request):
    """
    Remove the discount amount and coupon from the session.
    """
    try:
        cart = Cart(request)
        del request.session['coupon_id']
        request.session.modified = True
        
        # Recalculate prices without coupon
        cart.update_all_prices_from_database()
        
        storage = messages.get_messages(request)
        for message in storage:
            # Discard existing message
            pass
        messages.success(request, "Kuponki poistettu onnistuneesti.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    except KeyError:
        pass


def checkout(request):
    """
    Combined cart and checkout view
    Prices are automatically updated when Cart is initialized
    """
    cart = Cart(request)  # This automatically updates all prices and cleans coupons if needed
    
    # If cart is empty, show message
    if len(cart) == 0:
        messages.warning(request, "Ostoskorisi on tyhjä.")
    
    store_settings = StoreSettings.get_settings()
    applied_coupon = None

    # Handle coupon validation - cart already cleaned coupons if user changed group
    if 'coupon_id' in request.session:
        try:
            coupon = Coupon.objects.get(id=request.session['coupon_id'])
            user_for_validation = request.user if request.user.is_authenticated else None
            
            # Double-check group (should already be handled by Cart.__init__)
            if not cart.is_asiakas_group():
                # This should not happen normally, but as a safety measure
                del request.session['coupon_id']
                messages.error(request, "Kupongit eivät ole käytettävissä yritysasiakkaille.")
            elif coupon.is_valid(user_for_validation):
                applied_coupon = coupon
            else:
                del request.session['coupon_id']
                messages.error(request, "Kuponki on vanhentunut tai ei ole voimassa.")
        except Coupon.DoesNotExist:
            applied_coupon = None
            if 'coupon_id' in request.session:
                del request.session['coupon_id']

    # Handle coupon form submission
    if request.method == 'POST':
        if 'code' in request.POST:
            code = request.POST.get('code', '').strip()
            if code:
                try:
                    cart = Cart(request)  # Reinitialize to get current state
                    coupon = Coupon.objects.get(code=code)
                    min_purchase = coupon.min_purchase
                    subtotal_price = cart.get_subtotal_price()
                    
                    user_for_validation = request.user if request.user.is_authenticated else None
                    
                    # Check if user is in Asiakas group
                    if not cart.is_asiakas_group():
                        messages.error(request, "Kupongit eivät ole käytettävissä yritysasiakkaille.")
                    
                    # Validate coupon only for Asiakas group
                    elif coupon.is_valid(user_for_validation) and (min_purchase is None or subtotal_price >= min_purchase):
                        cart.apply_coupon_discount(request, coupon)
                        messages.success(request, f"Kuponki {code} käytetty onnistuneesti!")
                    else:
                        if coupon.single_use:
                            if coupon.used_by_anonymous:
                                messages.error(request, "Tämä kertakäyttökuponki on jo käytetty.")
                            elif request.user.is_authenticated and coupon.used_by.filter(id=request.user.id).exists():
                                messages.error(request, "Olet jo käyttänyt tämän kertakäyttökupongin.")
                            else:
                                messages.error(request, "Kuponki ei ole voimassa.")
                        elif min_purchase and subtotal_price < min_purchase:
                            messages.error(request, f"Ostoskorin summa on liian pieni tämän kupongin käyttöön. Vähimmäistilaus {min_purchase}€.")
                        else:
                            messages.error(request, "Kuponki ei ole voimassa.")
                except Coupon.DoesNotExist:
                    messages.error(request, "Kuponkia ei löydy.")
            
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

    has_cart_items = len(cart) > 0
    return render(request, 'cart/checkout.html', {
        'cart': cart,
        'store_settings': store_settings,
        'coupon': applied_coupon,
        'ga4_event': (
            build_cart_event(cart, 'begin_checkout')
            if has_cart_items else None
        ),
        'ga4_checkout_payload': (
            build_cart_params(cart) if has_cart_items else None
        ),
    })
