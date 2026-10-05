from django.db import models
from django.conf import settings
from shop.models import Product, Variant, Coupon, ShippingCost, GroupSettings, StoreSettings
from decimal import Decimal, ROUND_HALF_UP
import os
import barcode
from barcode.writer import ImageWriter

class Order(models.Model):
    STATUS_CHOICES = [
        ('new', 'Uusi'),
        ('processing', 'Käsittelyssä'),
        ('shipped', 'Lähetetty'),
        ('canceled', 'Peruttu'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('online', 'Verkkomaksu'),
        ('cod', 'Maksaa noudettaessa'),
    ]
    
    SHIPPING_METHOD_CHOICES = [
        ('pickup', 'Nouto myymälästä'),
        ('weight_based', 'Painoperusteinen toimitus'),
        ('postnord_lokero', 'Postnord palvelupiste'),
        ('postnord_kotiinkuljetus', 'Postnord Kotiinkuljetus'),
    ]
    
    status = models.CharField('Tila', max_length=20, choices=STATUS_CHOICES, default='new')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='orders', on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField('Etunimi', max_length=50, null=False)
    last_name = models.CharField('Sukunimi', max_length=50, null=False)
    email = models.EmailField('Sähköposti', max_length=50, null=False)
    address = models.CharField('Osoite', max_length=250, null=False)
    postal = models.CharField('Postinumero', max_length=20, null=False)
    city = models.CharField('Postitoimipaikka', max_length=100, null=False)
    phone = models.CharField('Puhelinnumero', max_length=100, null=False, blank=True)
    bill_address = models.CharField('Laskutus osoite', max_length=250, null=False, blank=True)
    bill_postal = models.CharField('Laskutus postinumero', max_length=20, null=False, blank=True)
    bill_city = models.CharField('Laskutus postitoimipaikka', max_length=100, null=False, blank=True)
    created = models.DateTimeField('Tehty', auto_now_add=True, null=False)
    updated = models.DateTimeField('Päivitetty', auto_now=True, null=False)
    notes = models.TextField('Muistiinpanot', max_length=200, null=True, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True)
    delivery_price = models.DecimalField('Toimitusmaksu', max_digits=10, decimal_places=2, default=0)
    payed = models.BooleanField('Maksettu', default=False)
    coupon = models.ForeignKey(Coupon, related_name='coupons', on_delete=models.SET_NULL, null=True, blank=True)
    payment_method = models.CharField('Maksutapa', max_length=20, choices=PAYMENT_METHOD_CHOICES, default='online')
    shipping_method = models.CharField('Toimitustapa', max_length=30, choices=SHIPPING_METHOD_CHOICES, default='weight_based')
    
    # Add these fields to store calculated prices
    subtotal_price = models.DecimalField('Välisumma', max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField('Loppusumma', max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ('-created',)
        verbose_name = 'Tilaus'
        verbose_name_plural = 'Tilaukset'

    def __init__(self, *args, **kwargs):
        self._discount_amount = Decimal('0')
        self._amount_discount = Decimal('0')
        self._free_shipping = False
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f'Tilaus {self.id} - {self.get_payment_method_display()}'

    def set_discount_from_request(self, request):
        """
        Load the discount code from session and check for discount from database
        """
        coupon_id = request.session.get('coupon_id')
        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id)
                self.coupon = coupon
                self._discount_amount = coupon.discount if coupon.discount else Decimal('0')
                self._amount_discount = coupon.amount if coupon.amount else Decimal('0')
                self._free_shipping = coupon.free_shipping
            except Coupon.DoesNotExist:
                self._free_shipping = False
                self._discount_amount = Decimal('0')
                self._amount_discount = Decimal('0')

    def _calculate_subtotal_price(self):
        """
        Calculate subtotal price from order items using get_cost() method
        """
        return sum(item.get_cost() for item in self.items.all())

    def get_subtotal_price(self):
        """
        Get the subtotal price of the order.
        For old orders without stored subtotal_price, calculate it
        """
        if self.subtotal_price > 0:
            return self.subtotal_price
        else:
            # Calculate for old orders
            return self._calculate_subtotal_price()

    def get_total_weight(self):
        """
        Get the total weight of the items in the order.
        """
        return sum(item.get_weight() for item in self.items.all())

    def _calculate_delivery_price(self):
        """
        Calculate delivery price based on shipping method and settings
        """
        from shop.models import StoreSettings
        
        # If free shipping is active, return 0
        if hasattr(self, '_free_shipping') and self._free_shipping:
            return Decimal('0.00')
            
        store_settings = StoreSettings.get_settings()
        subtotal = self.get_subtotal_price()
        
        # Check free shipping eligibility
        free_shipping_eligible = subtotal >= store_settings.free_shipping_threshold
        free_shipping_method = store_settings.free_shipping_method
        
        # Calculate price based on selected shipping method
        if self.shipping_method == 'weight_based':
            total_weight = self.get_total_weight()
            shipping_cost = ShippingCost.objects.filter(
                weight_from__lte=total_weight, 
                weight_to__gte=total_weight
            ).first()
            return Decimal('%.2f' % shipping_cost.price) if shipping_cost else Decimal('0.00')
            
        elif self.shipping_method == 'postnord_lokero':
            # Check if free shipping applies
            if free_shipping_eligible and free_shipping_method in ['postnord_lokero', 'both']:
                return Decimal('0.00')
            else:
                return store_settings.postnord_lokero_price
                
        elif self.shipping_method == 'postnord_kotiinkuljetus':
            # Check if free shipping applies
            if free_shipping_eligible and free_shipping_method in ['postnord_kotiinkuljetus', 'both']:
                return Decimal('0.00')
            else:
                return store_settings.postnord_kotiinkuljetus_price
                
        else:
            return Decimal('0.00')

    def get_delivery_price(self):
        """
        Get delivery price - for old orders without stored delivery_price, calculate it
        """
        if self.delivery_price > 0:
            return self.delivery_price
        else:
            # Calculate for old orders
            return self._calculate_delivery_price()

    def get_total_tax(self, request=None):
        """
        Get the total tax amount for the order.
        For compatibility, accept request parameter but don't use it
        """
        # Get the tax rate using the get_tax_rate method
        tax_rate = self.get_tax_rate()

        # Calculate tax amount in euros
        total_price = self.get_total_price()
        total_tax = tax_rate * total_price / (100 + tax_rate)

        return Decimal('%.2f' % total_tax)

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

    def _calculate_total_price(self):
        """
        Calculate total price including delivery and discounts
        """
        subtotal = self.get_subtotal_price()
        total_price = subtotal

        # Apply percentage discount
        discount_amount = Decimal('0')
        amount_discount = Decimal('0')
        free_shipping = False

        if self.coupon:
            discount_amount = self.coupon.discount if self.coupon.discount else Decimal('0')
            amount_discount = self.coupon.amount if self.coupon.amount else Decimal('0')
            free_shipping = self.coupon.free_shipping

        # Apply percentage discount
        if discount_amount > 0:
            discount = total_price * (discount_amount / Decimal('100'))
            total_price -= discount

        # Apply fixed amount discount
        if amount_discount > 0:
            total_price -= amount_discount

        # Add delivery price
        delivery_price = self._calculate_delivery_price() if free_shipping else self.get_delivery_price()
        total_price += delivery_price

        # Ensure the total price does not go below zero
        total_price = max(total_price, Decimal('0.00'))

        # Round to two decimal places
        total_price = total_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return total_price
    
    def get_total_price(self, request=None):
        """
        Calculate the total price of the order including tax, delivery, and discount.
        For old orders without stored total_price, calculate it
        """
        if self.total_price > 0:
            return self.total_price
        else:
            # Calculate for old orders
            return self._calculate_total_price()

    def is_paid(self):
        """
        Check if order is paid based on payment method
        """
        if self.payment_method == 'online':
            return self.payed
        else:
            # For cash on delivery, payment is handled upon delivery
            return False

    def get_payment_status_display(self):
        """
        Get display text for payment status
        """
        if self.payment_method == 'online':
            return 'Maksettu' if self.payed else 'Maksamatta'
        elif self.payment_method == 'cod':
            return 'Maksaa noudettaessa'
        return 'Tuntematon'

    # Additional methods for admin compatibility
    def get_coupon_code(self):
        """
        Get coupon code for display in admin
        """
        if self.coupon:
            return self.coupon.code
        return '-'

    def get_coupon_percentage_discount(self):
        """
        Get coupon percentage discount for display in admin
        """
        if self.coupon and self.coupon.discount:
            return f"-{self.coupon.discount}%"
        return '-'

    def get_coupon_amount_discount(self):
        """
        Get coupon amount discount for display in admin
        """
        if self.coupon and self.coupon.amount:
            return f"-{self.coupon.amount} €"
        return '-'

    def save(self, *args, **kwargs):
        """
        Override save - don't recalculate prices automatically
        Prices are set from cart during order creation
        """
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    variant = models.ForeignKey(Variant, related_name='order_items', on_delete=models.SET_NULL, null=True)
    barcode = models.BigIntegerField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    color = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    size = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    grain = models.CharField(max_length=2, blank=True, null=True)
    gloss = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    quantity = models.PositiveIntegerField(default=1)
    
    # Add fields to store color display data
    color_type = models.CharField(max_length=10, blank=True, null=True, help_text="Color palette type: color1 or color2")
    r = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Red component (0–255)")
    g = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Green component (0–255)")
    b = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Blue component (0–255)")
    thumbnail_url = models.CharField(max_length=500, blank=True, null=True, help_text="Thumbnail URL for color1")

    def __str__(self):
        try:
            if self.variant and self.variant.id:
                return f'{self.variant.item_description}'
            else:
                # Return basic info from stored fields
                product_info = []
                if self.color:
                    product_info.append(f"Väri: {self.color}")
                if self.size:
                    product_info.append(f"Koko: {self.size}")
                return f'Poistettu vaihtoehto ({", ".join(product_info)})'
        except Variant.DoesNotExist:
            # Return basic info from stored fields when variant doesn't exist
            product_info = []
            if self.color:
                product_info.append(f"Väri: {self.color}")
            if self.size:
                product_info.append(f"Koko: {self.size}")
            return f'Poistettu vaihtoehto ({", ".join(product_info)})'
    
    def get_unit_price(self):
        """
        Get the unit price of the order item.
        """
        if self.price is not None and self.quantity != 0:
            return self.price / self.quantity
        else:
            return 0

    def get_total_price(self):
        """
        Get the cost of the order item.
        """
        if self.price is not None and self.quantity != 0:
            return self.price
        else:
            return 0

    def get_cost(self):
        """
        Get the cost of the order item - alias for get_total_price() for compatibility
        """
        return self.get_total_price()

    def get_weight(self):
        """
        Get the weight of the order item.
        """
        if self.weight:
            return self.weight * self.quantity
        else:
            return Decimal('0')
    
    def get_color_display_data(self):
        """
        Get color display data for templates
        """
        try:
            if self.variant and self.variant.id:
                # If variant exists, get data from variant
                return {
                    'color': self.variant.color,
                    'color_type': self.variant.get_color_type(),
                    'r': self.variant.r,
                    'g': self.variant.g,
                    'b': self.variant.b,
                    'thumbnail_url': self.variant.get_thumbnail_url() if self.variant.get_color_type() == 'color1' else None
                }
        except Variant.DoesNotExist:
            pass
        
        # If variant is deleted or doesn't exist, use stored data
        return {
            'color': self.color,
            'color_type': self.color_type,
            'r': self.r,
            'g': self.g,
            'b': self.b,
            'thumbnail_url': self.thumbnail_url
        }
    
    def save(self, *args, **kwargs):
        """
        Save color display data when creating order item
        """
        try:
            if self.variant and self.variant.id:
                # Store color display data from variant
                self.color_type = self.variant.get_color_type()
                if self.variant.get_color_type() == 'color2':
                    self.r = self.variant.r
                    self.g = self.variant.g
                    self.b = self.variant.b
                elif self.variant.get_color_type() == 'color1':
                    self.thumbnail_url = self.variant.get_thumbnail_url()
        except Variant.DoesNotExist:
            # If variant doesn't exist, we can't get data from it
            pass
        
        super().save(*args, **kwargs)
    
    def generate_barcode_image(self):
        # Check if the barcode exists
        if self.barcode:
            # Create the filename based on the barcode number
            filename = f'{self.barcode}.png'
            # Define the directory where the barcode images will be stored
            directory = os.path.join(settings.MEDIA_ROOT, 'barcodes')
            # Define the full filepath
            filepath = os.path.join(directory, filename)

            # Check if the barcode image already exists
            if not os.path.exists(filepath):
                # Create the barcode object
                code = barcode.get_barcode_class('ean13')(str(self.barcode), writer=ImageWriter())

                # Create the directory if it doesn't exist
                if not os.path.exists(directory):
                    os.makedirs(directory)

                # Save the barcode image
                code.save(filepath)

            # Construct the URL for the image
            url = os.path.join(settings.MEDIA_URL, 'barcodes', filename)
            return url

        # Return None if no barcode exists
        return None