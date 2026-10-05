from django.contrib import admin
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.utils.safestring import mark_safe
from .models import Order, OrderItem
from shop.models import Variant

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    fields = ['variant', 'product_thumbnail', 'variant_size', 'variant_color', 'variant_grain', 'variant_gloss', 'variant_price', 'unit_price', 'quantity', 'total_price', 'barcode']
    readonly_fields = [ 'product_thumbnail', 'variant_size', 'variant_color', 'variant_grain', 'variant_gloss', 'variant_price', 'unit_price', 'quantity', 'total_price', 'barcode',]
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "variant":
            kwargs["widget"] = ForeignKeyRawIdWidget(db_field.remote_field, self.admin_site)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def barcode_image(self, obj):
        # Check if the barcode exists
        if obj.barcode:
            # Generate the URL for the barcode image
            url = obj.generate_barcode_image().replace("\\", "/")
            # Create the HTML for displaying the image
            return mark_safe(f'<img src="{url}.png" style="max-height: 150px;" />')

        # Return None if no barcode exists
        return None

    barcode_image.allow_tags = True
    barcode_image.short_description = 'Barcode'

    def product_thumbnail(self, obj):
        if obj.variant.product and obj.variant.product.thumbnail:
            return mark_safe('<img src="{0}" style="max-height:100px; max-width:100px;" />'.format(obj.variant.product.thumbnail.url))
        else:
            return None
    product_thumbnail.short_description = 'Product'
    
    def variant_size(self, obj):
        return obj.size
    variant_size.short_description = 'Size'

    def variant_price(self, obj):
        return f'{obj.variant.price}€'
    variant_price.short_description = 'List price'

    def variant_color(self, obj):
        return obj.color
    variant_color.short_description = 'Color'

    def variant_grain(self, obj):
        return obj.grain
    variant_grain.short_description = 'Grain'

    def variant_gloss(self, obj):
        return obj.gloss
    variant_gloss.short_description = 'Gloss'

    def unit_price(self, obj):
        return f'{obj.get_unit_price()}€'
    unit_price.short_description = 'Unit price'

    def total_price(self, obj):
        return f'{obj.get_total_price()}€'
    total_price.short_description = 'Total price'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'first_name', 'last_name',
                    'address', 'postal', 'city', 'payed', 'payment_method', 
                    'shipping_method', 'get_total_price_admin', 'created']
    list_filter = ['payed', 'created', 'updated', 'status', 'coupon', 'payment_method', 'shipping_method']
    search_fields = ['id', 'first_name', 'last_name', 'email', 'coupon__code', 'transaction_id']
    readonly_fields = ['transaction_id', 'get_subtotal_price', 'get_delivery_price', 
                       'get_total_tax_admin', 'get_total_price_admin', 'get_coupon_code', 
                       'get_coupon_percentage_discount', 'get_coupon_amount_discount',
                       'subtotal_price', 'total_price', 'delivery_price', 'created', 'updated']
    inlines = [OrderItemInline]

    fieldsets = (
        (None, {
            'fields': ('status', 'payment_method', 'shipping_method')
        }),
        ('Asiakastiedot', {
            'fields': ('user', 'first_name', 'last_name', 'email', 'phone')
        }),
        ('Toimitustiedot', {
            'fields': ('address', 'postal', 'city')
        }),
        ('Laskutustiedot', {
            'fields': ('bill_address', 'bill_postal', 'bill_city')
        }),
        ('Maksutiedot', {
            'fields': ('transaction_id', 'payed', 'coupon')
        }),
        ('Hinnat (laskettu automaattisesti)', {
            'fields': ('subtotal_price', 'delivery_price', 'total_price')
        }),
        ('Laskennalliset arvot (vain luku)', {
            'fields': ('get_subtotal_price', 'get_delivery_price', 'get_total_price_admin', 
                      'get_total_tax_admin', 'get_coupon_code', 
                      'get_coupon_percentage_discount', 'get_coupon_amount_discount')
        }),
    )

    def get_subtotal_price(self, obj): 
        """
        Display the total cost of the order excluding tax and delivery.
        """
        return f"{obj.get_subtotal_price()} €"
    get_subtotal_price.short_description = 'Välisumma (laskettu)'

    def get_delivery_price(self, obj):
        """
        Display delivery price for the order.
        """
        return f"{obj.get_delivery_price()} €"
    get_delivery_price.short_description = 'Toimitusmaksu (laskettu)'

    def get_total_price_admin(self, obj):
        """
        Display the total price of the order in the admin interface.
        """
        total_price = obj.get_total_price()
        return f"{total_price:.2f} €"
    get_total_price_admin.short_description = 'Yhteensä (laskettu)'
    
    def get_total_tax_admin(self, obj):
        """
        Display the total tax amount in euros for the order.
        """
        total_tax = obj.get_total_tax()
        return f"{total_tax} €"
    get_total_tax_admin.short_description = 'Josta arvonlisävero'
    
    def get_coupon_code(self, obj):
        """
        Display the coupon code for the order.
        """
        return obj.get_coupon_code()
    get_coupon_code.short_description = 'Kupongin koodi'

    def get_coupon_percentage_discount(self, obj):
        """
        Display the percentage discount for the order.
        """
        return obj.get_coupon_percentage_discount()
    get_coupon_percentage_discount.short_description = 'Kupongin prosenttialennus'

    def get_coupon_amount_discount(self, obj):
        """
        Display the fixed amount discount for the order.
        """
        return obj.get_coupon_amount_discount()
    get_coupon_amount_discount.short_description = 'Kupongin alennussumma'

    list_editable = ['status',]