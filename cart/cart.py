from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django.conf import settings
from shop.models import Product, Variant, ShippingCost, Tax, GroupSettings, Coupon, StoreSettings, Multiplier
from django.contrib import messages
from django.contrib.auth.models import Group

def convert_decimal_to_string(decimal_value):
    """Convert Decimal to string for JSON serialization"""
    if isinstance(decimal_value, Decimal):
        return str(decimal_value)
    return decimal_value

def convert_string_to_decimal(string_value):
    """Convert string back to Decimal"""
    try:
        return Decimal(string_value)
    except InvalidOperation:
        return Decimal('0')

class Cart():
    def __init__(self, request):
        self.request = request
        self.session = request.session
        self.user = request.user
        self.items = []
        # Use float instead of Decimal for session compatibility
        self.discount_amount = 0.0
        self.amount_discount = 0.0
        self.coupon = None
        self.free_shipping = False
        
        # Initialize with first available shipping method
        self.selected_shipping_method = self.get_first_available_shipping_method()

        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        
        # Load coupon code from session with group validation
        coupon_id = self.session.get('coupon_id')
        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id)
                
                # Check if user is still in Asiakas group
                if not self.is_asiakas_group():
                    # User changed group - remove coupon
                    if 'coupon_id' in self.session:
                        del self.session['coupon_id']
                    self.free_shipping = False
                    self.coupon = None
                    self.discount_amount = 0.0
                    self.amount_discount = 0.0
                    self.session.modified = True
                    
                    # Recalculate prices without coupon
                    self.update_all_prices_from_database()
                    
                else:
                    # User is still in Asiakas group - keep coupon
                    self.coupon = coupon
                    # Convert to float for session compatibility
                    self.discount_amount = float(coupon.discount) if coupon.discount else 0.0
                    self.amount_discount = float(coupon.amount) if coupon.amount else 0.0
                    self.free_shipping = coupon.free_shipping
                    
            except Coupon.DoesNotExist:
                # Coupon was deleted - clean up session
                if 'coupon_id' in self.session:
                    del self.session['coupon_id']
                self.free_shipping = False
                self.coupon = None
                self.discount_amount = 0.0
                self.amount_discount = 0.0
        
        # Load selected shipping method from session, or use first available
        saved_method = self.session.get('selected_shipping_method')
        if saved_method and self.is_shipping_method_available(saved_method):
            self.selected_shipping_method = saved_method
        else:
            # Use first available method if saved method is not available
            self.selected_shipping_method = self.get_first_available_shipping_method()
            self.session['selected_shipping_method'] = self.selected_shipping_method
            self.session.modified = True

        # ALWAYS update prices when cart is initialized
        self.update_all_prices_from_database()

    def update_all_prices_from_database(self):
        """
        Update all prices in cart from database
        This ensures prices are always current but WITHOUT coupon discounts
        """
        prices_updated = False
        items_to_remove = []
        
        for cart_key, item in self.cart.items():
            try:
                product_id, variant_id = cart_key.split('_')
                product_id = int(product_id)
                variant_id = int(variant_id) if variant_id != '0' else 0
                
                # Get current price from database WITHOUT coupon
                if variant_id > 0:
                    variant = Variant.objects.get(id=variant_id, product_id=product_id)
                    # Always calculate price WITHOUT coupon for item prices
                    current_price, discount_type = variant.calculate_best_discount_price(self.user, None)
                    product = variant.product
                else:
                    product = Product.objects.get(id=product_id)
                    # Always calculate price WITHOUT coupon for item prices
                    current_price, discount_type = product.calculate_best_discount_price(self.user, None)
                    variant = None
                
                # Always update price from database (no comparison needed)
                old_price = convert_string_to_decimal(item['price'])
                item['price'] = convert_decimal_to_string(current_price)
                
                # Update variant info with current data
                if variant:
                    variant_info = variant.get_cart_data()
                    variant_info.update({
                        'name': product.name,
                        'family': product.attributes.first().family if product.attributes.exists() else '',
                        'thumbnail': product.thumbnail.url if product.thumbnail else '',
                        'weight': str(variant.weight) if variant.weight else '0',
                        'product_id': str(product_id),
                        'product_name': product.name,
                        'product_url': product.get_absolute_url(),
                        'base_price': str(variant.price if variant else product.price),
                        'discount_percentage': product.discount_percentage,
                        'has_discount': discount_type == 'product',
                        'discount_type': discount_type,  # Store which discount was applied
                    })
                    item['variant_info'] = variant_info
                
                if abs(current_price - old_price) > Decimal('0.01'):
                    prices_updated = True
                    
            except (Product.DoesNotExist, Variant.DoesNotExist, ValueError) as e:
                items_to_remove.append(cart_key)
                continue
        
        # Remove invalid items after iteration
        for cart_key in items_to_remove:
            del self.cart[cart_key]
            prices_updated = True
        
        if prices_updated:
            self.save()
        
        return prices_updated

    def create_verified_order_data(self):
        """
        Create verified order data with prices from database
        This should be used when creating actual orders
        """
        # Ensure prices are up to date
        self.update_all_prices_from_database()
        
        verified_items = []
        total_price = Decimal('0')
        subtotal_without_coupon = Decimal('0')
        
        for cart_key, item in self.cart.items():
            try:
                product_id, variant_id = cart_key.split('_')
                product_id = int(product_id)
                variant_id = int(variant_id) if variant_id != '0' else 0
                quantity = item['quantity']
                
                # Get current price from database with best discount
                if variant_id > 0:
                    variant = Variant.objects.get(id=variant_id, product_id=product_id)
                    current_price, discount_type = variant.calculate_best_discount_price(self.user, self.coupon)
                    # Get price without coupon for subtotal
                    price_without_coupon, _ = variant.calculate_best_discount_price(self.user, None)
                    product = variant.product
                else:
                    product = Product.objects.get(id=product_id)
                    current_price, discount_type = product.calculate_best_discount_price(self.user, self.coupon)
                    # Get price without coupon for subtotal
                    price_without_coupon, _ = product.calculate_best_discount_price(self.user, None)
                    variant = None
                
                item_total = current_price * quantity
                total_price += item_total
                subtotal_without_coupon += price_without_coupon * quantity
                
                verified_items.append({
                    'product': product,
                    'variant': variant,
                    'quantity': quantity,
                    'unit_price': float(current_price),  # Convert to float for JSON
                    'total_price': float(item_total),    # Convert to float for JSON
                    'cart_key': cart_key,
                    'discount_type': discount_type
                })
                
            except (Product.DoesNotExist, Variant.DoesNotExist, ValueError) as e:
                continue
        
        # Apply coupon discounts only if coupon should be applied to total
        coupon_applied_to_total = False
        
        if self.should_apply_coupon_to_total():
            if self.discount_amount:
                discount_percentage = Decimal(str(self.discount_amount))
                discount_amount = total_price * (discount_percentage / Decimal('100'))
                total_price -= discount_amount
                coupon_applied_to_total = True
            
            if self.amount_discount:
                fixed_discount = Decimal(str(self.amount_discount))
                total_price -= fixed_discount
                coupon_applied_to_total = True
        
        # Add shipping - coupon free shipping only applies to postnord_lokero
        if self.free_shipping and self.selected_shipping_method == 'postnord_lokero':
            delivery_price = Decimal('0.00')
        elif coupon_applied_to_total and self.free_shipping and self.selected_shipping_method == 'postnord_lokero':
            delivery_price = Decimal('0.00')
        else:
            delivery_price = self.get_delivery_price()
        
        total_with_shipping = total_price + delivery_price
        
        return {
            'items': verified_items,
            'subtotal_before_coupon': float(subtotal_without_coupon),  # Price without coupon
            'subtotal_after_coupon': float(total_price),              # Price with coupon
            'shipping_price': float(delivery_price),                  # Convert to float
            'total_price': float(total_with_shipping),                # Convert to float
            'coupon': self.coupon,
            'discount_amount': self.discount_amount,
            'amount_discount': self.amount_discount,
            'free_shipping': (self.free_shipping and self.selected_shipping_method == 'postnord_lokero') or coupon_applied_to_total,
            'coupon_applied_to_total': coupon_applied_to_total
        }

    def get_first_available_shipping_method(self):
        """
        Get the first available shipping method from store settings
        """
        store_settings = StoreSettings.get_settings()
        
        # Check enabled methods in priority order (pickup moved to last)
        if store_settings.weight_based_enabled:
            return 'weight_based'
        elif store_settings.postnord_lokero_enabled:
            return 'postnord_lokero'
        elif store_settings.postnord_kotiinkuljetus_enabled:
            return 'postnord_kotiinkuljetus'
        elif store_settings.pickup_enabled:
            return 'pickup'
        else:
            return 'weight_based'  # Fallback

    def is_shipping_method_available(self, method):
        """
        Check if a shipping method is available based on store settings
        """
        store_settings = StoreSettings.get_settings()
        
        if method == 'pickup':
            return store_settings.pickup_enabled
        elif method == 'weight_based':
            return store_settings.weight_based_enabled
        elif method == 'postnord_lokero':
            return store_settings.postnord_lokero_enabled
        elif method == 'postnord_kotiinkuljetus':
            return store_settings.postnord_kotiinkuljetus_enabled
        else:
            return False

    def get_group_settings(self, user=None):
        """Get group settings for price calculations"""
        # Initialize group_settings with default values
        group_settings = GroupSettings(
            tax=Tax(rate=Decimal('0')), 
            multiplier=Multiplier(multi=Decimal('1'))
        )

        # Check if the user is authenticated
        user_to_check = user or self.user
        if user_to_check and user_to_check.is_authenticated:
            if user_to_check.groups.exists():
                user_group = user_to_check.groups.first()
                try:
                    group_settings = GroupSettings.objects.get(group=user_group)
                except GroupSettings.DoesNotExist:
                    pass
            else:
                default_group_name = "Asiakas"
                try:
                    user_group = Group.objects.get(name=default_group_name)
                    group_settings = GroupSettings.objects.get(group=user_group)
                except (Group.DoesNotExist, GroupSettings.DoesNotExist):
                    pass
        else:
            default_group_name = "Asiakas"
            try:
                user_group = Group.objects.get(name=default_group_name)
                group_settings = GroupSettings.objects.get(group=user_group)
            except (Group.DoesNotExist, GroupSettings.DoesNotExist):
                pass

        return group_settings

    def is_asiakas_group(self, user=None):
        """
        Check if user belongs to Asiakas group
        """
        user_to_check = user or self.user
        
        if not user_to_check or not user_to_check.is_authenticated:
            return True  # Default to Asiakas for anonymous users
        
        if user_to_check.groups.exists():
            user_group = user_to_check.groups.first()
            return user_group.name == "Asiakas"
        else:
            return True  # No group assigned, default to Asiakas

    def calculate_best_discount_price(self, base_price, product, user=None, coupon=None):
        """Calculate price with the best available discount using multiplier system"""
        group_settings = self.get_group_settings(user)
        base_multi = Decimal(group_settings.multiplier.multi)

        # Use the appropriate tax and multiplier values
        tax_multiplier = Decimal(1 + group_settings.tax.rate / 100)

        # Check if user is in Asiakas group
        is_asiakas = self.is_asiakas_group(user)
        
        if is_asiakas:
            # ASIAKAS GROUP LOGIC: Product discounts and coupons allowed
            # Calculate all possible discounted prices
            prices = []
            
            # 1. Product discount (always has highest priority)
            if product.discount_percentage > 0:
                product_discount_percentage = Decimal(product.discount_percentage) / 100
                product_discounted_price = base_price * (1 - product_discount_percentage)
                product_final_price = product_discounted_price * tax_multiplier * base_multi * Decimal(product.multiplier)
                prices.append(('product', round(product_final_price, 2), product.discount_percentage))
            
            # 2. Group discount price (always available)
            group_final_price = base_price * tax_multiplier * base_multi * Decimal(product.multiplier)
            prices.append(('group', round(group_final_price, 2), 0))
            
            # 3. Coupon discount (only if valid and NO product discount exists)
            coupon_discount_percentage = 0
            if coupon and coupon.is_valid(user) and coupon.discount and product.discount_percentage == 0:
                # Only apply coupon if product doesn't have its own discount
                coupon_discount_percentage = coupon.discount
                
                # Get default group multiplier for Asiakas
                default_group_name = "Asiakas"
                try:
                    default_group = Group.objects.get(name=default_group_name)
                    default_group_settings = GroupSettings.objects.get(group=default_group)
                    default_multi = Decimal(default_group_settings.multiplier.multi)
                except (Group.DoesNotExist, GroupSettings.DoesNotExist):
                    default_multi = Decimal('2.0')
                
                # Calculate coupon price based on DEFAULT group price, not current group price
                coupon_discount_decimal = Decimal(coupon_discount_percentage) / 100
                
                # Start from default group price (Asiakas), then apply coupon
                price_with_default_group = base_price * default_multi
                coupon_discounted_price = price_with_default_group * (1 - coupon_discount_decimal)
                coupon_final_price = coupon_discounted_price * tax_multiplier * Decimal(product.multiplier)
                
                # Only add coupon price if it's better than current group price
                if coupon_final_price < group_final_price:
                    prices.append(('coupon', round(coupon_final_price, 2), coupon_discount_percentage))
            
            # Return the price with the highest discount (lowest price)
            best_price = min(prices, key=lambda x: x[1])
            return best_price[1], best_price[0]
        
        else:
            # OTHER GROUPS LOGIC: Only group discount, no product discounts, no coupons
            # Calculate group discount percentage compared to default Asiakas group
            default_group_name = "Asiakas"
            try:
                default_group = Group.objects.get(name=default_group_name)
                default_group_settings = GroupSettings.objects.get(group=default_group)
                default_multi = Decimal(default_group_settings.multiplier.multi)
                group_discount_percentage = (1 - (base_multi / default_multi)) * 100
            except (Group.DoesNotExist, GroupSettings.DoesNotExist):
                default_multi = Decimal('2.0')
                group_discount_percentage = (1 - (base_multi / default_multi)) * 100
            
            # Only apply group discount for other groups
            group_final_price = base_price * tax_multiplier * base_multi * Decimal(product.multiplier)
            
            return group_final_price, 'group'

    def should_apply_coupon_to_total(self):
        """
        Check if coupon should be applied to total price
        For Asiakas group only, and only if no product discounts present
        """
        # Coupons are only for Asiakas group
        if not self.is_asiakas_group():
            return False
        
        if not self.coupon or not self.coupon.is_valid(self.user):
            return False
        
        # Check if any items have product discounts (coupon shouldn't apply to total)
        if any(item.get('variant_info', {}).get('discount_type') == 'product' 
            for item in self.cart.values()):
            return False
        
        # Check if any items already have coupon discounts applied at item level
        if any(item.get('variant_info', {}).get('discount_type') == 'coupon' 
            for item in self.cart.values()):
            # If coupon is already applied at item level, don't apply to total
            return False
        
        # For fixed amount discounts, always apply to total
        if self.amount_discount:
            return True
        
        # For percentage discounts, check if it's better than group discount
        if self.discount_amount:
            group_settings = self.get_group_settings()
            base_multi = Decimal(group_settings.multiplier.multi)
            
            # Get default group multiplier
            default_group_name = "Asiakas"
            try:
                default_group = Group.objects.get(name=default_group_name)
                default_group_settings = GroupSettings.objects.get(group=default_group)
                default_multi = Decimal(default_group_settings.multiplier.multi)
            except (Group.DoesNotExist, GroupSettings.DoesNotExist):
                default_multi = Decimal('2.0')
            
            # Calculate group discount percentage
            group_discount_percentage = (1 - (base_multi / default_multi)) * 100
            
            # If group discount is better than or equal to coupon discount, don't apply coupon to total
            if group_discount_percentage >= self.coupon.discount:
                return False
        
        return True

    def get_coupon_status(self):
        """
        Get detailed information about coupon application without recursion
        """
        # Coupons are only for Asiakas group
        if not self.is_asiakas_group():
            return {
                'applied': False, 
                'reason': 'Not Asiakas group',
                'details': 'Kupongit eivät ole käytettävissä yritysasiakkaille'
            }
        
        if not self.coupon:
            return {'applied': False, 'reason': 'No coupon'}
        
        if not self.coupon.is_valid(self.user):
            return {'applied': False, 'reason': 'Coupon not valid'}
        
        # Simple check - if we have any coupon-related discounts configured
        has_coupon_discount = self.discount_amount > 0 or self.amount_discount > 0
        
        if not has_coupon_discount:
            return {'applied': False, 'reason': 'No coupon discount', 'details': 'Kuponkia ei ole käytössä'}
        
        # Check if there are product discounts in cart
        has_product_discounts = any(
            item.get('variant_info', {}).get('discount_type') == 'product' 
            for item in self.cart.values()
        )
        
        if has_product_discounts:
            return {
                'applied': True,  # Changed to True because coupon is partially applied
                'reason': 'Product discounts present',
                'details': 'Kuponki on käytössä vain tuotteisiin, joilla ei ole omaa alennusta',
                'partial_application': True
            }
        
        # Check if coupon should be applied to total
        should_apply_to_total = self.should_apply_coupon_to_total()
        
        return {
            'applied': True,
            'reason': 'Coupon applied to total' if should_apply_to_total else 'Coupon applied to items',
            'details': f'Kuponki {self.coupon.discount if self.coupon.discount else self.coupon.amount} on käytössä',
            'applied_to_total': should_apply_to_total
        }

    def get_subtotal_with_group_discounts(self):
        """
        Calculate subtotal price with only group and product discounts, no coupon
        This recalculates prices without considering coupon
        """
        subtotal_price = Decimal('0')
        
        for cart_key, item in self.cart.items():
            try:
                product_id, variant_id = cart_key.split('_')
                product_id = int(product_id)
                variant_id = int(variant_id) if variant_id != '0' else 0
                
                # Get price without coupon
                if variant_id > 0:
                    variant = Variant.objects.get(id=variant_id, product_id=product_id)
                    # Calculate price with None as coupon to exclude coupon discounts
                    current_price, discount_type = variant.calculate_best_discount_price(self.user, None)
                else:
                    product = Product.objects.get(id=product_id)
                    # Calculate price with None as coupon to exclude coupon discounts
                    current_price, discount_type = product.calculate_best_discount_price(self.user, None)
                
                item_quantity = item.get('quantity', 0)
                subtotal_price += current_price * item_quantity
                
            except (Product.DoesNotExist, Variant.DoesNotExist, ValueError) as e:
                continue
        
        return subtotal_price

    def get_subtotal_with_coupon_applied_to_items(self):
        """
        Calculate subtotal with coupon applied only to items without product discounts
        For Asiakas group only
        """
        subtotal_price = Decimal('0')
        
        for cart_key, item in self.cart.items():
            try:
                product_id, variant_id = cart_key.split('_')
                product_id = int(product_id)
                variant_id = int(variant_id) if variant_id != '0' else 0
                
                # Get price with coupon applied (coupon will only be applied to items without product discounts)
                if variant_id > 0:
                    variant = Variant.objects.get(id=variant_id, product_id=product_id)
                    current_price, discount_type = variant.calculate_best_discount_price(self.user, self.coupon)
                else:
                    product = Product.objects.get(id=product_id)
                    current_price, discount_type = product.calculate_best_discount_price(self.user, self.coupon)
                
                item_quantity = item.get('quantity', 0)
                subtotal_price += current_price * item_quantity
                
            except (Product.DoesNotExist, Variant.DoesNotExist, ValueError) as e:
                continue
        
        return subtotal_price

    def get_display_subtotal(self):
        """
        Get the subtotal to display in the cart - with group discounts but without coupon
        """
        return self.get_subtotal_with_group_discounts()

    def get_coupon_discount_amount(self):
        """
        Calculate how much discount the coupon would apply
        Returns the discount amount in euros
        """
        # Coupons are only for Asiakas group
        if not self.is_asiakas_group():
            return Decimal('0')
        
        if not self.coupon or not self.coupon.is_valid(self.user):
            return Decimal('0')
        
        # If there are product discounts in cart, coupon should only apply to items without discounts
        has_product_discounts = any(
            item.get('variant_info', {}).get('discount_type') == 'product' 
            for item in self.cart.values()
        )
        
        if has_product_discounts:
            # Calculate discount only on items without product discounts
            subtotal_for_coupon = Decimal('0')
            
            for cart_key, item in self.cart.items():
                try:
                    product_id, variant_id = cart_key.split('_')
                    product_id = int(product_id)
                    variant_id = int(variant_id) if variant_id != '0' else 0
                    
                    # Get price without coupon to check discount type
                    if variant_id > 0:
                        variant = Variant.objects.get(id=variant_id, product_id=product_id)
                        price_without_coupon, discount_type = variant.calculate_best_discount_price(self.user, None)
                    else:
                        product = Product.objects.get(id=product_id)
                        price_without_coupon, discount_type = product.calculate_best_discount_price(self.user, None)
                    
                    # Only include items without product discounts in coupon calculation
                    if discount_type != 'product':
                        item_quantity = item.get('quantity', 0)
                        subtotal_for_coupon += price_without_coupon * item_quantity
                        
                except (Product.DoesNotExist, Variant.DoesNotExist, ValueError) as e:
                    continue
            
            # Calculate discount based on coupon type
            discount_amount = Decimal('0')
            
            if self.discount_amount:
                discount_percentage = Decimal(str(self.discount_amount))
                discount_amount = subtotal_for_coupon * (discount_percentage / Decimal('100'))
                # Убираем округление до целых чисел, оставляем 2 знака после запятой
                discount_amount = discount_amount.quantize(Decimal('0.01'))
            
            if self.amount_discount:
                fixed_discount = Decimal(str(self.amount_discount))
                discount_amount += fixed_discount
                discount_amount = discount_amount.quantize(Decimal('0.01'))
        
        else:
            # No product discounts - calculate discount on full subtotal
            subtotal_without_coupon = self._get_subtotal_without_coupon_cached()
            
            # Calculate discount based on coupon type
            discount_amount = Decimal('0')
            
            if self.discount_amount:
                discount_percentage = Decimal(str(self.discount_amount))
                discount_amount = subtotal_without_coupon * (discount_percentage / Decimal('100'))
                # Убираем округление до целых чисел, оставляем 2 знака после запятой
                discount_amount = discount_amount.quantize(Decimal('0.01'))
            
            if self.amount_discount:
                fixed_discount = Decimal(str(self.amount_discount))
                discount_amount += fixed_discount
                discount_amount = discount_amount.quantize(Decimal('0.01'))
        
        return discount_amount

    def _get_subtotal_without_coupon_cached(self):
        """
        Helper method to calculate subtotal without coupon without causing recursion
        """
        subtotal_price = Decimal('0')
        
        for cart_key, item in self.cart.items():
            try:
                product_id, variant_id = cart_key.split('_')
                product_id = int(product_id)
                variant_id = int(variant_id) if variant_id != '0' else 0
                
                # Get price without coupon
                if variant_id > 0:
                    variant = Variant.objects.get(id=variant_id, product_id=product_id)
                    price_without_coupon, _ = variant.calculate_best_discount_price(self.user, None)
                else:
                    product = Product.objects.get(id=product_id)
                    price_without_coupon, _ = product.calculate_best_discount_price(self.user, None)
                
                item_quantity = item.get('quantity', 0)
                subtotal_price += price_without_coupon * item_quantity
                
            except (Product.DoesNotExist, Variant.DoesNotExist, ValueError) as e:
                continue
        
        return subtotal_price.quantize(Decimal('0.01'))

    def get_detailed_discount_info(self):
        """
        Get detailed information about all discounts in cart
        """
        discount_info = {
            'has_product_discounts': False,
            'has_group_discount': False,
            'has_coupon_discount': False,
            'product_discount_items': [],
            'group_discount_percentage': 0,
            'coupon_status': self.get_coupon_status(),
            'total_savings': Decimal('0.00'),
        }
        
        # Calculate group discount
        group_settings = self.get_group_settings()
        base_multi = Decimal(group_settings.multiplier.multi)
        default_group_name = "Asiakas"
        try:
            default_group = Group.objects.get(name=default_group_name)
            default_group_settings = GroupSettings.objects.get(group=default_group)
            default_multi = Decimal(default_group_settings.multiplier.multi)
            group_discount_percentage = (1 - (base_multi / default_multi)) * 100
            discount_info['group_discount_percentage'] = round(group_discount_percentage, 1)
            discount_info['has_group_discount'] = group_discount_percentage > 0
        except (Group.DoesNotExist, GroupSettings.DoesNotExist):
            pass
        
        # Check for product discounts (only for Asiakas group)
        if self.is_asiakas_group():
            for item in self.cart.values():
                discount_type = item.get('variant_info', {}).get('discount_type', 'group')
                if discount_type == 'product':
                    discount_info['has_product_discounts'] = True
                    product_name = item.get('variant_info', {}).get('name', 'Unknown')
                    discount_percentage = item.get('variant_info', {}).get('discount_percentage', 0)
                    discount_info['product_discount_items'].append({
                        'name': product_name,
                        'discount_percentage': discount_percentage
                    })
        
        # Check if coupon is applied (only for Asiakas group)
        discount_info['has_coupon_discount'] = discount_info['coupon_status']['applied']
        
        # Calculate total savings
        subtotal_without_any_discounts = self.get_subtotal_without_any_discounts()
        current_subtotal = self.get_subtotal_with_group_discounts()
        discount_info['total_savings'] = subtotal_without_any_discounts - current_subtotal
        
        return discount_info

    def get_subtotal_without_any_discounts(self):
        """
        Calculate subtotal price without any discounts (Asiakas group prices)
        """
        subtotal_price = Decimal('0')
        
        for cart_key, item in self.cart.items():
            try:
                product_id, variant_id = cart_key.split('_')
                product_id = int(product_id)
                variant_id = int(variant_id) if variant_id != '0' else 0
                
                # Get base price without any discounts
                if variant_id > 0:
                    variant = Variant.objects.get(id=variant_id, product_id=product_id)
                    base_price = variant.price
                    product = variant.product
                else:
                    product = Product.objects.get(id=product_id)
                    base_price = product.price
                
                # Calculate price with default Asiakas group multiplier
                default_group_name = "Asiakas"
                try:
                    default_group = Group.objects.get(name=default_group_name)
                    default_group_settings = GroupSettings.objects.get(group=default_group)
                    default_multi = Decimal(default_group_settings.multiplier.multi)
                except (Group.DoesNotExist, GroupSettings.DoesNotExist):
                    default_multi = Decimal('2.0')
                
                # Apply default multiplier and tax
                group_settings = self.get_group_settings()
                tax_multiplier = Decimal(1 + group_settings.tax.rate / 100)
                
                if variant_id > 0:
                    product_multiplier = Decimal(product.multiplier)
                else:
                    product_multiplier = Decimal(product.multiplier)
                
                final_price = base_price * tax_multiplier * default_multi * product_multiplier
                item_quantity = item.get('quantity', 0)
                subtotal_price += final_price * item_quantity
                
            except (Product.DoesNotExist, Variant.DoesNotExist, ValueError) as e:
                continue
        
        return subtotal_price
    
    def get_subtotal_without_coupon(self):
        """
        Calculate subtotal without any coupon discounts
        """
        subtotal_price = Decimal('0')
        
        for cart_key, item in self.cart.items():
            try:
                product_id, variant_id = cart_key.split('_')
                product_id = int(product_id)
                variant_id = int(variant_id) if variant_id != '0' else 0
                
                # Get price without coupon
                if variant_id > 0:
                    variant = Variant.objects.get(id=variant_id, product_id=product_id)
                    price_without_coupon, _ = variant.calculate_best_discount_price(self.user, None)
                else:
                    product = Product.objects.get(id=product_id)
                    price_without_coupon, _ = product.calculate_best_discount_price(self.user, None)
                
                item_quantity = item.get('quantity', 0)
                subtotal_price += price_without_coupon * item_quantity
                
            except (Product.DoesNotExist, Variant.DoesNotExist, ValueError) as e:
                continue
        
        return subtotal_price.quantize(Decimal('0.01'))

    def get_active_discounts_summary(self):
        """
        Get summary of active discounts for display
        """
        discount_info = self.get_detailed_discount_info()
        summary = []
        
        # Only show product discounts for Asiakas group
        if self.is_asiakas_group() and discount_info['has_product_discounts']:
            for product in discount_info['product_discount_items']:
                # Округляем процент скидки товара до целого числа
                discount_percentage = int(round(product['discount_percentage']))
                summary.append(f"Tuotealennus: -{discount_percentage}%")
        
        if discount_info['has_group_discount'] and discount_info['group_discount_percentage'] > 0:
            # Округляем процент групповой скидки до целого числа
            group_discount = int(round(discount_info['group_discount_percentage']))
            summary.append(f"Henkilökohtainen alennus: -{group_discount}%")
        
        # Only show coupon discounts for Asiakas group
        if self.is_asiakas_group() and discount_info['has_coupon_discount']:
            if self.discount_amount:
                # Округляем процент скидки купона до целого числа
                coupon_discount = int(round(self.discount_amount))
                summary.append(f"Kupongin alennus: -{coupon_discount}%")
            if self.amount_discount:
                summary.append(f"Kupongin alennus: -{self.amount_discount}€")
        
        return summary

    def add(self, product, variant, quantity=1, update_quantity=False):
        """
        Add a product to the cart or update its quantity.
        Calculate price with best available discount
        """
        product_id = str(product.id)
        variant_id = str(variant.id) if variant and variant.id else '0'

        # Calculate price with best available discount
        if variant and variant.id:
            # Use variant price with best discount
            base_price = variant.price
            calculated_price, discount_type = self.calculate_best_discount_price(base_price, product, self.user, self.coupon)
        else:
            # Use product price with best discount
            base_price = product.price
            calculated_price, discount_type = self.calculate_best_discount_price(base_price, product, self.user, self.coupon)

        if variant_id != '0':
            cart_key = f"{product_id}_{variant_id}"
            try:
                variant_instance = Variant.objects.get(id=variant_id)
                # Use the new get_cart_data method and store ALL variant data in session
                variant_info = variant_instance.get_cart_data()
                # Add additional fields that might be needed
                variant_info.update({
                    'name': product.name,
                    'family': product.attributes.first().family if product.attributes.exists() else '',
                    'thumbnail': product.thumbnail.url if product.thumbnail else '',
                    'weight': str(variant_instance.weight) if variant_instance.weight else '0',
                    'product_id': product_id,
                    'product_name': product.name,
                    'product_url': product.get_absolute_url(),
                    'base_price': str(base_price),  # Store base price for reference
                    'discount_percentage': product.discount_percentage,
                    'has_discount': discount_type == 'product',
                    'discount_type': discount_type,  # Store which discount was applied
                })
            except Variant.DoesNotExist:
                variant_info = {
                    'id': 0,
                    'color': '',
                    'color_type': '',
                    'name': product.name,
                    'family': product.attributes.first().family if product.attributes.exists() else '',
                    'thumbnail': product.thumbnail.url if product.thumbnail else '',
                    'weight': '0',
                    'base_price': str(base_price),
                    'discount_percentage': product.discount_percentage,
                    'has_discount': discount_type == 'product',
                    'discount_type': discount_type,
                    'product_id': product_id,
                    'product_name': product.name,
                    'product_url': product.get_absolute_url(),
                }
        else:
            cart_key = f"{product_id}_0"
            variant_info = {
                'id': 0,
                'color': '',
                'color_type': '',
                'name': product.name,
                'family': product.attributes.first().family if product.attributes.exists() else '',
                'thumbnail': product.thumbnail.url if product.thumbnail else '',
                'weight': '0',
                'base_price': str(base_price),
                'discount_percentage': product.discount_percentage,
                'has_discount': discount_type == 'product',
                'discount_type': discount_type,
                'product_id': product_id,
                'product_name': product.name,
                'product_url': product.get_absolute_url(),
            }

        if cart_key not in self.cart:
            self.cart[cart_key] = {
                'quantity': 0,
                'price': convert_decimal_to_string(calculated_price),  # Use calculated price with best discount
                'variant_info': variant_info
            }

        if update_quantity:
            self.cart[cart_key]['quantity'] = quantity
        else:
            self.cart[cart_key]['quantity'] += quantity

        self.save()

    def set_user(self, user):
        """
        Set the current user for the cart and recalculate all prices
        Also handle coupon cleanup if user group changed
        """
        old_user = self.user
        self.user = user
        
        # If user changed, check if group changed and handle coupons
        if old_user != user:
            old_is_asiakas = self._is_user_asiakas(old_user) if old_user else True
            new_is_asiakas = self.is_asiakas_group()
            
            # If user changed from Asiakas to non-Asiakas, remove coupon
            if old_is_asiakas and not new_is_asiakas and self.coupon:
                if 'coupon_id' in self.session:
                    del self.session['coupon_id']
                self.coupon = None
                self.discount_amount = 0.0
                self.amount_discount = 0.0
                self.free_shipping = False
                self.session.modified = True
            
            # Recalculate all prices in cart
            self.update_all_prices_from_database()

    def _is_user_asiakas(self, user):
        """
        Helper method to check if a specific user is in Asiakas group
        """
        if not user or not user.is_authenticated:
            return True  # Default to Asiakas for anonymous users
        
        if user.groups.exists():
            user_group = user.groups.first()
            return user_group.name == "Asiakas"
        else:
            return True  # No group assigned, default to Asiakas

    def set_shipping_method(self, method):
        """
        Set the selected shipping method and force save to session
        """
        if self.is_shipping_method_available(method):
            self.selected_shipping_method = method
            self.session['selected_shipping_method'] = method
            self.session.modified = True  # Force session save
            self.save()  # Call the save method to ensure persistence
        else:
            # If method is not available, use first available method
            available_method = self.get_first_available_shipping_method()
            self.selected_shipping_method = available_method
            self.session['selected_shipping_method'] = available_method
            self.session.modified = True
            self.save()

    def save(self):
        """
        Mark the session as "modified" to ensure it gets saved.
        Convert all data to JSON-serializable types.
        """
        try:
            # Create a deep copy of cart data and convert all values to serializable types
            def make_serializable(obj):
                """Recursively convert all objects to JSON-serializable types"""
                if isinstance(obj, dict):
                    return {k: make_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [make_serializable(item) for item in obj]
                elif isinstance(obj, Decimal):
                    return str(obj)
                elif isinstance(obj, (int, float, str, bool)) or obj is None:
                    return obj
                else:
                    # Convert any other object to string
                    return str(obj)
            
            # Convert cart to serializable format
            cart_serializable = make_serializable(self.cart)
            
            # Store in session
            self.session[settings.CART_SESSION_ID] = cart_serializable
            
            # Ensure other session values are serializable
            if 'selected_shipping_method' in self.session:
                self.session['selected_shipping_method'] = str(self.session['selected_shipping_method'])
            
            if 'coupon_id' in self.session:
                self.session['coupon_id'] = int(self.session['coupon_id']) if self.session['coupon_id'] else None
            
            self.session.modified = True
            
        except Exception as e:
            # If there's an error, try to clear problematic data
            try:
                # Create a minimal safe cart
                safe_cart = {}
                for key, value in self.cart.items():
                    if isinstance(key, str):
                        safe_cart[key] = {
                            'quantity': int(value.get('quantity', 0)),
                            'price': str(value.get('price', '0')),
                            'variant_info': {
                                k: str(v) for k, v in value.get('variant_info', {}).items()
                            }
                        }
                self.session[settings.CART_SESSION_ID] = safe_cart
                self.session.modified = True
            except Exception as safe_error:
                # Last resort - clear the cart
                if settings.CART_SESSION_ID in self.session:
                    del self.session[settings.CART_SESSION_ID]

    def remove_group(self, product_id, variant_id):
        """
        Remove a group of products with the same ID and size variant from the cart.
        """
        group_key = f"{product_id}_{variant_id}"
        if group_key in self.cart:
            del self.cart[group_key]
            self.save()

    def apply_coupon_discount(self, request, coupon):
        """
        Apply a coupon discount to the cart WITHOUT changing item prices
        """
        # Coupons are only for Asiakas group
        if not self.is_asiakas_group():
            messages.error(request, "Kupongit eivät ole käytettävissä yritysasiakkaille.")
            if 'coupon_id' in self.session:
                del self.session['coupon_id']
            return
        
        user_for_validation = request.user if request.user.is_authenticated else None
        
        if coupon.is_valid(user_for_validation):
            subtotal = self.get_subtotal_price()
            if coupon.min_purchase and subtotal < coupon.min_purchase:
                messages.error(request, "Ostoskorin summa on liian pieni tämän kupongin käyttöön.")
                if 'coupon_id' in self.session:
                    del self.session['coupon_id']
                return
            
            try:
                # Only store coupon ID in session, don't mark as used yet
                request.session['coupon_id'] = coupon.id
                self.coupon = coupon
                # Convert to float for session compatibility - use safe conversion
                self.discount_amount = float(coupon.discount) if coupon.discount else 0.0
                self.amount_discount = float(coupon.amount) if coupon.amount else 0.0
                self.free_shipping = coupon.free_shipping
                request.session.modified = True
                
                # DO NOT recalculate item prices - coupon is applied only to total
                # self.update_all_prices_from_database()  # REMOVE THIS LINE
                
            except Exception as e:
                messages.error(request, "Kupongin käyttö epäonnistui.")
        else:
            if coupon.single_use:
                if coupon.used_by_anonymous:
                    messages.error(request, "Tämä kertakäyttökuponki on jo käytetty.")
                else:
                    messages.error(request, "Olet jo käyttänyt tämän kertakäyttökupongin.")
            else:
                messages.error(request, "Kuponki on vanhentunut tai ei ole voimassa.")
            
            if 'coupon_id' in self.session:
                del self.session['coupon_id']
        
        self.save()

    def __iter__(self):
        """
        Iterate over the items in the cart using data stored in session.
        No database queries - all data should be in session.
        Returns simple dictionaries instead of objects.
        """
        # Update prices before iteration to ensure they are current
        self.update_all_prices_from_database()
        
        # Create a list of cart items to avoid modification during iteration
        cart_items = list(self.cart.items())
        
        for item_key, item in cart_items:
            # Skip if item was removed during iteration
            if item_key not in self.cart:
                continue
                
            # Create a simple dictionary with all needed data for templates
            product_data = {
                'id': int(item_key.split('_')[0]),
                'name': item['variant_info'].get('name', ''),
                'thumbnail_url': item['variant_info'].get('thumbnail', ''),
                'get_absolute_url': item['variant_info'].get('product_url', f"/product/{int(item_key.split('_')[0])}/"),
            }
            
            # Store product data as simple dictionary instead of object
            item['product_data'] = product_data
            
            # Ensure variant_info has all required fields
            variant_info = item['variant_info']
            if 'price' not in variant_info:
                variant_info['price'] = item.get('price', '0')
            
            # Calculate prices and weights
            try:
                variant_info_price = convert_string_to_decimal(variant_info.get('price', '0'))
                quantity = item['quantity']
                
                # Calculate total price for the quantity
                total_price = variant_info_price * quantity
                item['total_price'] = str(total_price.quantize(Decimal('0.01')))

                variant_info_weight = convert_string_to_decimal(variant_info.get('weight', '0'))
                item['total_weight'] = str((variant_info_weight * quantity).quantize(Decimal('0.01')))

                # Add discount information for display (only for Asiakas group)
                if self.is_asiakas_group():
                    item['is_asiakas_group'] = True
                    item['has_discount'] = variant_info.get('has_discount', False)
                    item['discount_percentage'] = variant_info.get('discount_percentage', 0)
                    item['discount_type'] = variant_info.get('discount_type', 'regular')
                    
                    if item['has_discount']:
                        # Calculate original price per unit before discount for display
                        base_price_per_unit = convert_string_to_decimal(variant_info.get('base_price', '0'))
                        
                        # Calculate Asiakas group price per unit for comparison
                        try:
                            asiakas_group = Group.objects.get(name="Asiakas")
                            asiakas_settings = GroupSettings.objects.get(group=asiakas_group)
                            tax_multiplier = Decimal(1 + asiakas_settings.tax.rate / 100)
                            asiakas_multi = Decimal(asiakas_settings.multiplier.multi)
                            product_multiplier = Decimal(variant_info.get('product_multiplier', '1'))
                            
                            # Calculate Asiakas price per unit
                            asiakas_price_per_unit = base_price_per_unit * tax_multiplier * asiakas_multi * product_multiplier
                            asiakas_price_per_unit = asiakas_price_per_unit.quantize(Decimal('0.01'))
                            
                            # Calculate total original price for the quantity
                            original_price_total = asiakas_price_per_unit * quantity
                            item['original_price'] = str(original_price_total.quantize(Decimal('0.01')))
                            
                        except (Group.DoesNotExist, GroupSettings.DoesNotExist):
                            # Fallback if Asiakas group not found
                            original_price_total = base_price_per_unit * quantity
                            item['original_price'] = str(original_price_total.quantize(Decimal('0.01')))
                    else:
                        # No discount, original price is the same as current price
                        item['original_price'] = item['total_price']
                        
                else:
                    # For other groups, show comparison with Asiakas price
                    item['is_asiakas_group'] = False
                    item['has_discount'] = False
                    item['discount_percentage'] = 0
                    item['discount_type'] = 'group'
                    
                    # Calculate Asiakas group price for comparison
                    base_price_per_unit = convert_string_to_decimal(variant_info.get('base_price', '0'))
                    try:
                        asiakas_group = Group.objects.get(name="Asiakas")
                        asiakas_settings = GroupSettings.objects.get(group=asiakas_group)
                        tax_multiplier = Decimal(1 + asiakas_settings.tax.rate / 100)
                        asiakas_multi = Decimal(asiakas_settings.multiplier.multi)
                        product_multiplier = Decimal(variant_info.get('product_multiplier', '1'))
                        
                        # Calculate Asiakas price per unit
                        asiakas_price_per_unit = base_price_per_unit * tax_multiplier * asiakas_multi * product_multiplier
                        asiakas_price_per_unit = asiakas_price_per_unit.quantize(Decimal('0.01'))
                        
                        # Calculate total Asiakas price for the quantity
                        asiakas_price_total = asiakas_price_per_unit * quantity
                        item['original_price'] = str(asiakas_price_total.quantize(Decimal('0.01')))
                        
                    except (Group.DoesNotExist, GroupSettings.DoesNotExist):
                        # Fallback if Asiakas group not found
                        asiakas_price_total = base_price_per_unit * quantity
                        item['original_price'] = str(asiakas_price_total.quantize(Decimal('0.01')))
                        
            except (InvalidOperation, ValueError) as e:
                # Skip this item if there are calculation errors
                print(f"Error calculating prices for item {item_key}: {e}")
                continue

            yield item

    def __len__(self):
        """
        Count all items in the cart.
        """
        return sum(
            group.get('quantity', group) if isinstance(group, dict) else group
            for group in self.cart.values()
        )
    
    def get_subtotal_price(self):
        """
        Calculate the total cost of the items in the cart.
        Uses only session data, no database queries.
        """
        subtotal_price = Decimal('0')

        for item in self.cart.values():
            item_quantity = item.get('quantity', 0)
            # Get price from variant_info if available, otherwise from item
            if 'variant_info' in item and 'price' in item['variant_info']:
                try:
                    variant_info_price = convert_string_to_decimal(item['variant_info'].get('price', '0'))
                    subtotal_price += variant_info_price * item_quantity
                except (InvalidOperation, ValueError):
                    continue
            else:
                try:
                    variant_info_price = convert_string_to_decimal(item.get('price', '0'))
                    subtotal_price += variant_info_price * item_quantity
                except (InvalidOperation, ValueError):
                    continue

        return subtotal_price
    
    def validate_coupon(self):
        """
        Validate the coupon and set the corresponding values in the cart.
        """
        # Coupons are only for Asiakas group
        if not self.is_asiakas_group():
            if self.coupon:
                storage = messages.get_messages(self.request)
                for message in storage:
                    # Discard existing message
                    pass
                messages.error(self.request, "Kupongit eivät ole käytettävissä yritysasiakkaille. Alennus ei käytössä.")
                self.discount_amount = 0.0
                self.amount_discount = 0.0
                self.free_shipping = False
                if 'coupon_id' in self.session:
                    del self.session['coupon_id']
                
                # Recalculate prices without coupon
                self.update_all_prices_from_database()
            return
        
        if self.coupon:
            user_for_validation = self.user if self.user.is_authenticated else None
            if not self.coupon.is_valid(user_for_validation):
                storage = messages.get_messages(self.request)
                for message in storage:
                    # Discard existing message
                    pass
                
                if self.coupon.single_use:
                    if self.coupon.used_by_anonymous:
                        messages.error(self.request, "Tämä kertakäyttökuponki on jo käytetty. Alennus ei käytössä.")
                    else:
                        messages.error(self.request, "Olet jo käyttänyt tämän kertakäyttökupongin. Alennus ei käytössä.")
                else:
                    messages.error(self.request, "Kuponki ei ole enää voimassa. Alennus ei käytössä.")
                
                self.discount_amount = 0.0
                self.amount_discount = 0.0
                self.free_shipping = False
                if 'coupon_id' in self.session:
                    del self.session['coupon_id']
                
                # Recalculate prices without coupon
                self.update_all_prices_from_database()
                    
            elif self.coupon.min_purchase and self.get_subtotal_price() < self.coupon.min_purchase:
                storage = messages.get_messages(self.request)
                for message in storage:
                    # Discard existing message
                    pass
                messages.error(self.request, "Ostoskorin summa on liian pieni tämän kupongin käyttöön. Alennus ei käytössä.")
                self.discount_amount = 0.0
                self.amount_discount = 0.0
                self.free_shipping = False

    def get_total_price(self):
        """
        Calculate the total cost of the items in the cart.
        Uses only session data, no database queries.
        """
        self.validate_coupon()

        # Check if there are product discounts in cart
        has_product_discounts = any(
            item.get('variant_info', {}).get('discount_type') == 'product' 
            for item in self.cart.values()
        )
        
        if has_product_discounts:
            # If there are product discounts, coupon is applied only to items without discounts
            # So we use the subtotal with coupon applied to items
            total_price = self.get_subtotal_with_coupon_applied_to_items()
        else:
            # No product discounts - coupon can be applied to total
            total_price = self.get_subtotal_with_group_discounts()
            
            # Apply coupon discounts to total ONLY if it should be applied
            if self.should_apply_coupon_to_total():
                # Apply percentage discount to total
                if self.discount_amount:
                    discount_percentage = Decimal(str(self.discount_amount))
                    discount_amount = total_price * (discount_percentage / Decimal('100'))
                    total_price -= discount_amount

                # Apply fixed amount discount to total
                if self.amount_discount:
                    fixed_discount = Decimal(str(self.amount_discount))
                    total_price -= fixed_discount

        # Add delivery price - coupon free shipping only applies to postnord_lokero
        if self.free_shipping and self.selected_shipping_method == 'postnord_lokero':
            delivery_price = Decimal('0.00')
        else:
            delivery_price = self.get_delivery_price()
        
        total_price += delivery_price

        # Round to two decimal places
        total_price = total_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_price = max(total_price, Decimal('0.00'))
        
        return total_price

    def get_modal_total_price(self):
        """
        Calculate the total price for modal display (with discounts but without shipping)
        Uses only session data, no database queries.
        """
        self.validate_coupon()

        # Start with subtotal
        total_price = self.get_subtotal_with_group_discounts()

        # Apply coupon discounts to total ONLY if it should be applied
        if self.should_apply_coupon_to_total():
            # Apply percentage discount
            if self.discount_amount:
                discount_percentage = Decimal(str(self.discount_amount))
                discount_amount = total_price * (discount_percentage / Decimal('100'))
                total_price -= discount_amount

            # Apply fixed amount discount
            if self.amount_discount:
                fixed_discount = Decimal(str(self.amount_discount))
                total_price -= fixed_discount

        # Round to two decimal places
        total_price = total_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        total_price = max(total_price, Decimal('0.00'))
        
        return total_price
    
    def get_tax_rate(self):
        """
        Get the tax rate for users.
        """
        # Use Decimal for fixed tax rate
        fixed_tax_rate = Decimal('25.5')  # Default tax rate as Decimal

        # Check if a user is provided and is authenticated
        if self.user and self.user.is_authenticated:
            # If authenticated, get the user's group settings
            if self.user.groups.exists():
                # If authenticated and has groups, get the first group
                user_group = self.user.groups.first()
                try:
                    group_settings = GroupSettings.objects.get(group=user_group)
                    # Ensure tax_rate is a Decimal
                    tax_rate = group_settings.tax.rate if group_settings.tax else fixed_tax_rate
                except GroupSettings.DoesNotExist:
                    # Handle the case where group settings do not exist for the user's group
                    tax_rate = fixed_tax_rate
            else:
                # If authenticated but has no groups, use the regular user's fixed tax rate
                tax_rate = fixed_tax_rate
        else:
            # If not authenticated, use the regular user's fixed tax rate
            tax_rate = fixed_tax_rate

        return tax_rate

    def get_total_tax(self):
        """
        Calculate the total tax amount in euros based on the tax rate for the user's group.
        """
        # Get the tax rate using the get_tax_rate method
        tax_rate = self.get_tax_rate()

        # Calculate tax amount in euros
        total_tax = tax_rate * self.get_total_price() / (100 + tax_rate)

        return Decimal('%.2f' % total_tax) 
        
    def get_total_weight(self):
        """
        Calculate the total weight of the items in the cart.
        Uses only session data, no database queries.
        """
        total_weight = Decimal('0')

        for item in self.cart.values():
            # Check if 'variant_info' key exists in the item dictionary
            if 'variant_info' in item:
                item_weight = convert_string_to_decimal(item['variant_info'].get('weight', '0'))
                item_quantity = Decimal(item.get('quantity', 0))
                total_weight += item_weight * item_quantity

        return total_weight

    def get_shipping_methods(self):
        """
        Get available shipping methods with prices
        """
        store_settings = StoreSettings.get_settings()
        subtotal = self.get_subtotal_price()
        
        # Check which shipping methods are enabled
        weight_based_enabled = store_settings.weight_based_enabled
        lokero_enabled = store_settings.postnord_lokero_enabled
        kotiinkuljetus_enabled = store_settings.postnord_kotiinkuljetus_enabled
        pickup_enabled = store_settings.pickup_enabled
        
        # Check free shipping eligibility based on settings
        free_shipping_eligible = subtotal >= store_settings.free_shipping_threshold
        free_shipping_method = store_settings.free_shipping_method
        
        # Determine which methods get free shipping
        # Coupon free shipping only applies to lokero (palvelupiste), not kotiinkuljetus
        lokero_free = (free_shipping_eligible and 
                    free_shipping_method in ['postnord_lokero', 'both']) or self.free_shipping
        kotiinkuljetus_free = (free_shipping_eligible and 
                            free_shipping_method in ['postnord_kotiinkuljetus', 'both'])
        # Coupon free shipping does NOT apply to kotiinkuljetus
        
        methods = {}
        
        # Add Weight Based Shipping if enabled (moved to first)
        if weight_based_enabled:
            methods['weight_based'] = {
                'name': 'Painoperusteinen toimitus',
                'price': self.get_weight_based_delivery_price(),
                'description': f'Toimitus painon mukaan - {self.get_weight_based_delivery_price()}€',
                'free_shipping_eligible': False,
                'is_free': False,
                'enabled': True
            }
        
        # Add Postnord palvelupiste if enabled
        if lokero_enabled:
            methods['postnord_lokero'] = {
                'name': 'Postnord Palvelupiste',
                'original_price': store_settings.postnord_lokero_price,
                'price': Decimal('0.00') if lokero_free else store_settings.postnord_lokero_price,
                'description': 'Postnord Palvelupiste - nouto noutopisteeltä',
                'free_shipping_eligible': True,
                'is_free': lokero_free,
                'enabled': True
            }
        
        # Add Postnord Kotiinkuljetus if enabled
        if kotiinkuljetus_enabled:
            methods['postnord_kotiinkuljetus'] = {
                'name': 'Postnord Kotiinkuljetus',
                'original_price': store_settings.postnord_kotiinkuljetus_price,
                'price': Decimal('0.00') if kotiinkuljetus_free else store_settings.postnord_kotiinkuljetus_price,
                'description': 'Postnord Kotiinkuljetus - kotiin tai työpaikalle',
                'free_shipping_eligible': True,
                'is_free': kotiinkuljetus_free,
                'enabled': True
            }
        
        # Add Pickup method if enabled (moved to last)
        if pickup_enabled:
            methods['pickup'] = {
                'name': 'Nouto myymälästä',
                'price': Decimal('0.00'),  # Pickup is always free
                'description': 'Nouto myymälästä - ilmainen',
                'free_shipping_eligible': False,
                'is_free': True,  # Pickup is always free
                'enabled': True
            }
        
        return methods

    def get_delivery_price(self):
        """
        Calculate the delivery price based on selected shipping method
        """
        # Check if free shipping applies to the selected method
        if self.free_shipping:
            # Free shipping from coupon only applies to postnord_lokero, not kotiinkuljetus
            if self.selected_shipping_method == 'postnord_lokero':
                return Decimal('0.00')
            # For other methods, check regular free shipping eligibility
            elif self.selected_shipping_method == 'postnord_kotiinkuljetus':
                # For kotiinkuljetus, only apply free shipping if eligible by store settings
                store_settings = StoreSettings.get_settings()
                subtotal = self.get_subtotal_price()
                free_shipping_eligible = subtotal >= store_settings.free_shipping_threshold
                free_shipping_method = store_settings.free_shipping_method
                kotiinkuljetus_free = (free_shipping_eligible and 
                                    free_shipping_method in ['postnord_kotiinkuljetus', 'both'])
                if kotiinkuljetus_free:
                    return Decimal('0.00')
        
        shipping_methods = self.get_shipping_methods()
        
        if self.selected_shipping_method in shipping_methods:
            price = shipping_methods[self.selected_shipping_method]['price']
            return price
        else:
            # If selected method not available, use first available method
            if shipping_methods:
                first_method = list(shipping_methods.keys())[0]
                price = shipping_methods[first_method]['price']
                return price
            else:
                return Decimal('0.00')

    def get_weight_based_delivery_price(self):
        """
        Calculate the delivery price based on the total weight of items in the cart.
        """
        total_weight = self.get_total_weight()

        # logic to fetch the appropriate shipping cost based on the total weight
        shipping_cost = ShippingCost.objects.filter(weight_from__lte=total_weight, weight_to__gte=total_weight).first()

        if shipping_cost:
            return Decimal('%.2f' % shipping_cost.price)
        else:
            # Handle the case where no shipping cost is defined for the given weight
            return Decimal(0)

    def clear(self):
        """
        Remove the cart from the session.
        """
        if settings.CART_SESSION_ID in self.session:
            # Clear the cart dictionary
            self.cart.clear()
            del self.session[settings.CART_SESSION_ID]

        if 'coupon_id' in self.session:
            del self.session['coupon_id']

        if 'selected_shipping_method' in self.session:
            del self.session['selected_shipping_method']

        # Mark the session as modified and save it
        self.session.modified = True
        self.save()