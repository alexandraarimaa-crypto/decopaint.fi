from django.db import models
from django.urls import reverse
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.validators import MaxValueValidator, MinValueValidator 
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django.contrib.auth.models import Group
from users.models import CustomUser
from decimal import Decimal
from tinymce.models import HTMLField
from django.utils.translation import gettext_lazy as _
from mptt.models import MPTTModel, TreeForeignKey
from django.db.models import Avg
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


MATERIAL_CALCULATOR_COVERAGE_UNITS = (
    ('m2_per_l', 'm²/l'),
    ('m2_per_kg', 'm²/kg'),
    ('l_per_m2', 'l/m²'),
    ('kg_per_m2', 'kg/m²'),
)

MATERIAL_CALCULATOR_PACKAGE_UNITS = (
    ('l', 'l'),
    ('kg', 'kg'),
)

class PriceUpdateFile(models.Model):
    file = models.FileField(upload_to="price_updates/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Hintojen päivitys'
        verbose_name_plural = 'Hintojen päivitys' 
        ordering = ['id']

    def __str__(self):
        return f"Tiedosto ladattu {self.uploaded_at}"

class Slider(models.Model):
    active = models.BooleanField('Aktiivinen', default=True)
    title = HTMLField('Otsikko', blank=False)
    info = HTMLField('Teksti', blank=True)
    link_text = models.CharField('Linkin teksti', max_length=200, blank=True, default='')
    link = models.URLField('Linkki', blank=True)
    image = models.ImageField('Taustakuva', upload_to='slider_images', blank=True)
    order = models.IntegerField('Järjestys', blank=False, default=0)

    class Meta:
        verbose_name = 'Kuvaesitys'
        verbose_name_plural = 'Kuvaesitykset' 
        ordering = ['order']  # Устанавливаем порядок сортировки по полю order

    def process_image(self):
        if self.image:
            # Open the original image
            original_img = Image.open(self.image)

            max_size = (1920, 1080)
            original_img.thumbnail(max_size)

            # Save the original image back to the field
            image_io = BytesIO()
            if self.image.name.lower().endswith('.png'):
                # Preserve transparency for PNG images
                original_img.save(image_io, format='PNG', optimize=True)
                image_extension = 'png'
            else:
                # Convert to RGB for JPEG images
                if original_img.mode == 'RGBA':
                    original_img = original_img.convert('RGB')
                original_img.save(image_io, format='JPEG', quality=85)  # JPEG quality
                image_extension = 'jpg'

            # Check if the image has already been saved
            if not self.image.name:
                # Generate a unique filename based on the current date and time
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                image_name = f"{timestamp}_{self.id}.{image_extension}"
            else:
                # Keep the original filename
                image_name = self.image.name

            self.image = InMemoryUploadedFile(
                image_io,
                'ImageField',
                image_name,
                f'image/{image_extension}',
                image_io.tell,
                None
            )

    def save(self, *args, **kwargs):
        self.process_image()  # Обработка изображения
        if not self.order:  # Если поле order не заполнено
            # Получаем максимальное значение поля order из базы данных и увеличиваем его на 1
            max_order = Slider.objects.aggregate(models.Max('order'))['order__max']
            self.order = max_order + 1 if max_order is not None else 1  # Если база данных пустая, устанавливаем 1
        super().save(*args, **kwargs)  # Вызываем метод save() родительского класса для сохранения объекта

class StoreSettings(models.Model):
    email = models.EmailField(blank=True, default='')
    open_time = HTMLField('Aukioloajat', blank=True, default='')
    terms = HTMLField('Käyttöehdot', blank=True, default='')
    top_bar = HTMLField('Tärkeä tieto / Yläpalkki', blank=True, default='')
    company_terms = HTMLField('Myyntiehdot yrityksille', blank=True, default='')
    
    # Shipping settings
    weight_based_enabled = models.BooleanField(
        'Painoperusteinen toimitus käytössä', 
        default=True
    )
    postnord_lokero_enabled = models.BooleanField(
        'Postnord palvelupiste käytössä', 
        default=True
    )
    postnord_lokero_price = models.DecimalField(
        'Postnord palvelupiste hinta', 
        max_digits=10, 
        decimal_places=2, 
        default=10.00
    )
    
    postnord_kotiinkuljetus_enabled = models.BooleanField(
        'Postnord Kotiinkuljetus käytössä', 
        default=True
    )
    postnord_kotiinkuljetus_price = models.DecimalField(
        'Postnord Kotiinkuljetus hinta', 
        max_digits=10, 
        decimal_places=2, 
        default=15.00
    )
    
    # NEW FIELD: Pickup method
    pickup_enabled = models.BooleanField(
        'Nouto myymälästä käytössä', 
        default=True
    )
    
    free_shipping_threshold = models.DecimalField(
        'Ilmaisen toimituksen kynnys', 
        max_digits=10, 
        decimal_places=2, 
        default=100.00
    )
    free_shipping_method = models.CharField(
        'Ilmainen toimitus menetelmä',
        max_length=40,
        choices=[
            ('postnord_lokero', 'Postnord palvelupiste'),
            ('postnord_kotiinkuljetus', 'Postnord Kotiinkuljetus'),
            ('both', 'Molemmat Postnord-toimitukset'),
        ],
        default='postnord_lokero'
    )
    
    class Meta:
        verbose_name = 'Kaupan asetukset'
        verbose_name_plural = 'Kaupan asetukset'

    def __str__(self):
        return f'Kaupan asetukset'

    @classmethod
    def get_settings(cls):
        """Get store settings singleton"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

class Category(MPTTModel):
    active = models.BooleanField(default=True, verbose_name='Aktiivinen')
    invert_colors = models.BooleanField(default=False, verbose_name='Käännä värit')
    name = models.CharField(max_length=200, db_index=True, default='', verbose_name='Nimi')
    slug = models.SlugField(max_length=200, unique=True, verbose_name='Slug')
    bg_image = models.ImageField(upload_to='category_images', blank=True, null=True, verbose_name='Taustakuva')
    title = models.TextField(blank=True, default='', verbose_name='Otsikko')
    info = HTMLField(blank=True, default='', verbose_name='Teksti')
    keyword = models.TextField(blank=True, default='', help_text='Pilkuilla erotetut avainsanat', verbose_name='Avainsanat')
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children', verbose_name='Yläkategoria')

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        ordering = ('name',)
        verbose_name = 'Tuotekategoria'
        verbose_name_plural = 'Tuotekategoriat'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_list_by_category', args=[self.slug])
    
    def process_image(self):
        if self.bg_image:
            # Open the original image
            original_img = Image.open(self.bg_image)

            # Set the max size for the image
            max_size = (1920, 1080)
            original_img.thumbnail(max_size)

            # Check if the image has an alpha channel (transparency)
            if original_img.mode == 'RGBA':
                # Preserve transparency
                image_mode = 'RGBA'
            else:
                # Convert to RGB for JPEG and non-transparent images
                original_img = original_img.convert('RGB')
                image_mode = 'RGB'

            # Save the original image back to the field
            image_io = BytesIO()
            if self.bg_image.name.lower().endswith('.png'):
                # Preserve transparency for PNG images when converting to WEBP
                original_img.save(image_io, format='WEBP', optimize=True)
                image_extension = 'webp'
            else:
                # For non-PNG images, save as WEBP
                original_img.save(image_io, format='WEBP', quality=95, optimize=True)
                image_extension = 'webp'

            # Generate a unique image name
            image_name = f"{slugify(self.name)}_{self.id}.{image_extension}"

            self.bg_image = InMemoryUploadedFile(
                image_io,
                'ImageField',
                image_name,
                f'image/{image_extension}',
                image_io.tell(),
                None
            )

    def save(self, *args, **kwargs):
        if not self.pk or (self.bg_image and self.bg_image != self.__class__.objects.get(pk=self.pk).bg_image):
            self.process_image()  # Process the image if it's new or changed
        super().save(*args, **kwargs)  # Save the object
    
class ShippingCost(models.Model):
    weight_from = models.DecimalField(max_digits=10, decimal_places=2)
    weight_to = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Toimitus'
        verbose_name_plural = 'Toimitusmaksut'

    def __str__(self):
        return f"{self.weight_from}kg - {self.weight_to}kg: {self.price}€"
    
class Tax(models.Model):
    name = models.CharField(max_length=255)
    rate = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        verbose_name = 'Vero'
        verbose_name_plural = 'Verot'

    def __str__(self):
        return f"{self.name} - {self.rate}%"
    
class Multiplier(models.Model):
    multi = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(limit_value=1.00)]
    )

    class Meta:
        verbose_name = 'Kerroin'
        verbose_name_plural = 'Kertoimet'

    def __str__(self):
        return f"x{self.multi}"

class Effect(models.Model):
    # Link to related product
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='effects')

    # Name of the effect
    name = models.CharField(max_length=50, verbose_name="Nimi", default='')

    # Image representing the effect
    photo = models.ImageField(upload_to='effects_photos/', verbose_name="Kuva")

    # Description of how the effect is applied
    application_method = models.CharField(max_length=255, verbose_name="Käyttöohjeet")

    # Coverage in square meters per liter
    coverage = models.CharField(max_length=50, verbose_name="Peittoala m²/l")

    # Tools used for the base coat
    tools_base = models.CharField(max_length=255, verbose_name="Työkalut peruskerrokseen")

    # Tools used for the final coat
    tools_finish = models.CharField(max_length=255, verbose_name="Työkalut viimeistelykerrokseen")

    # Dilution instructions
    dilution = models.CharField(max_length=100, verbose_name="Laimennus")

    def save(self, *args, **kwargs):
        # Save first to generate ID (needed for filename)
        super().save(*args, **kwargs)
        self.process_image()
        # Save again with processed image
        super().save(*args, **kwargs)

    def process_image(self):
        if self.photo:
            img = Image.open(self.photo)
            img = img.convert('RGB')  # Ensure consistent format
            img = img.resize((859, 404), Image.LANCZOS)  # Resize to fixed dimensions

            image_io = BytesIO()
            img.save(image_io, format='WEBP', quality=95, optimize=True)

            image_name = f"{slugify(self.product.name)}_effect_{self.id}.webp"

            self.photo = InMemoryUploadedFile(
                image_io,
                'ImageField',
                image_name,
                'image/webp',
                image_io.tell(),
                None
            )

    class Meta:
        verbose_name = 'Efekti'
        verbose_name_plural = 'Efektit'

    def __str__(self):
        return f"Effect for {self.product.name}: {self.application_method}"
    
class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True, default='')
    slug = models.SlugField(max_length=200, default='')
    image = models.ImageField(upload_to='tags', blank=True)
    info = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tagit'
    
    def __str__(self):
        return self.name

    def process_image(self):
        if self.image:
            # Open the original image
            original_img = Image.open(self.image)

            # Set the max size for the image
            max_size = (1000, 1000)
            original_img.thumbnail(max_size)

            # Check if the image has an alpha channel (transparency)
            if original_img.mode == 'RGBA':
                # Preserve transparency
                image_mode = 'RGBA'
            else:
                # Convert to RGB for JPEG and non-transparent images
                original_img = original_img.convert('RGB')
                image_mode = 'RGB'

            # Save the original image back to the field
            image_io = BytesIO()
            if self.image.name.lower().endswith('.png'):
                # Preserve transparency for PNG images when converting to WEBP
                original_img.save(image_io, format='WEBP', optimize=True)
                image_extension = 'webp'
            else:
                # For non-PNG images, save as WEBP
                original_img.save(image_io, format='WEBP', quality=95, optimize=True)
                image_extension = 'webp'

            # Generate a unique image name
            image_name = f"{slugify(self.name)}_{self.id}.{image_extension}"

            self.image = InMemoryUploadedFile(
                image_io,
                'ImageField',
                image_name,
                f'image/{image_extension}',
                image_io.tell(),
                None
            )

            # Create a thumbnail
            thumbnail_size = (540, int((540 / original_img.width) * original_img.height))  # Maintain aspect ratio
            thumbnail_img = original_img.resize(thumbnail_size, resample=Image.LANCZOS)

            thumbnail_io = BytesIO()
            thumbnail_img.save(thumbnail_io, format='WEBP', quality=95, optimize=True)

            thumbnail_name = f"{slugify(self.name)}_{self.id}_thumbnail.{image_extension}"

            self.thumbnail = InMemoryUploadedFile(
                thumbnail_io,
                'ImageField',
                thumbnail_name,
                f'image/{image_extension}',
                thumbnail_io.tell(),
                None
            )

    def save(self, *args, **kwargs):
        # Process the image only if it's a new image or has been modified
        if not self.pk or (self.image and self.image != self.__class__.objects.get(pk=self.pk).image):
            self.process_image()
        super().save(*args, **kwargs)


class Product(models.Model):
    available = models.BooleanField(default=True)
    name = models.CharField(max_length=200, db_index=True, default='')
    slug = models.SlugField(max_length=200, db_index=True, blank=True, default='')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    multiplier = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(limit_value=0.10)]
    )
    discount_percentage = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    category = models.ManyToManyField(Category, related_name='products', blank=True)
    sku = models.CharField(max_length=200, db_index=True, blank=True, default='')
    image = models.ImageField(upload_to='products/', blank=True)
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True)
    description = HTMLField(blank=True, default='')
    tech_info = HTMLField(blank=True, default='')
    properties = HTMLField(blank=True, default='')
    material_calculator_manual_enabled = models.BooleanField(
        default=False,
        verbose_name='Muokkaa menekkilaskuria käsin',
        help_text='Käytä alla olevia tuotekohtaisia arvoja automaattisen laskennan sijaan.'
    )
    material_calculator_coverage_min = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name='Riittoisuus / menekki min'
    )
    material_calculator_coverage_max = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name='Riittoisuus / menekki max'
    )
    material_calculator_unit = models.CharField(
        max_length=12,
        choices=MATERIAL_CALCULATOR_COVERAGE_UNITS,
        blank=True,
        default='',
        verbose_name='Riittoisuuden yksikkö'
    )
    
    # New fields for palette selection
    use_color1_palette = models.BooleanField(
        default=False, 
        verbose_name='Käytä Color1-palettia',
        help_text='Näytä perinteiset värit kuvilla'
    )
    use_color2_palette = models.BooleanField(
        default=True, 
        verbose_name='Käytä Color2-palettia',
        help_text='Näytä uudet värit RGB-arvoilla'
    )
    palette_priority = models.CharField(
        max_length=10,
        choices=[
            ('color2', 'Color2 ensin'),
            ('color1', 'Color1 ensin')
        ],
        default='color2',
        verbose_name='Palettien prioriteetti',
        help_text='Miten paletit näytetään asiakkaille'
    )
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField(Tag, related_name='products', blank=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Tuote'
        verbose_name_plural = 'Tuotteet'

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        minimum = self.material_calculator_coverage_min
        maximum = self.material_calculator_coverage_max
        if minimum and maximum and maximum < minimum:
            raise ValidationError({
                'material_calculator_coverage_max': 'Maksimiarvon pitää olla vähintään minimiarvo.'
            })

    def decrease_stock_quantity(self, quantity):
        self.stock -= quantity
        self.save()

    def increase_stock_quantity(self, quantity):
        self.stock += quantity
        self.save()


    def is_asiakas_group(self, user=None):
        """
        Check if user belongs to Asiakas group
        """
        if not user or not user.is_authenticated:
            return True  # Default to Asiakas for anonymous users
        
        if user.groups.exists():
            user_group = user.groups.first()
            return user_group.name == "Asiakas"
        else:
            return True  # No group assigned, default to Asiakas
            
    def calculate_best_discount_price(self, user=None, coupon=None):
        """Calculate price with the best available discount using multiplier system"""
        group_settings = self.get_group_settings(user)
        base_multi = Decimal(group_settings.multiplier.multi)

        # Use the appropriate tax and multiplier values
        tax_multiplier = Decimal(1 + group_settings.tax.rate / 100)

        base_price = self.price
        
        # Check if user is in Asiakas group
        is_asiakas = self.is_asiakas_group(user)
        
        if is_asiakas:
            # ASIAKAS GROUP LOGIC: Product discounts and coupons allowed
            # Calculate all possible discounted prices
            prices = []
            
            # 1. Product discount (always has highest priority)
            if self.discount_percentage > 0:
                product_discount_percentage = Decimal(self.discount_percentage) / 100
                product_discounted_price = base_price * (1 - product_discount_percentage)
                product_final_price = product_discounted_price * tax_multiplier * base_multi * self.multiplier
                prices.append(('product', round(product_final_price, 2)))
            
            # 2. Group discount price (always available)
            group_final_price = base_price * tax_multiplier * base_multi * self.multiplier
            prices.append(('group', round(group_final_price, 2)))
            
            # 3. Coupon discount (only if valid and NO product discount exists)
            coupon_discount_percentage = 0
            if coupon and coupon.is_valid(user) and coupon.discount and self.discount_percentage == 0:
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
                coupon_final_price = coupon_discounted_price * tax_multiplier * self.multiplier
                
                # Only add coupon price if it's better than current group price
                if coupon_final_price < group_final_price:
                    prices.append(('coupon', round(coupon_final_price, 2)))
            
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
            group_final_price = base_price * tax_multiplier * base_multi * self.multiplier
            
            return group_final_price, 'group'

    def get_discount_info(self, user=None, coupon=None):
        """
        Get detailed discount information for display
        """
        group_settings = self.get_group_settings(user)
        base_multi = Decimal(group_settings.multiplier.multi)
        
        # Get default group multiplier for comparison
        default_group_name = "Asiakas"
        try:
            default_group = Group.objects.get(name=default_group_name)
            default_group_settings = GroupSettings.objects.get(group=default_group)
            default_multi = Decimal(default_group_settings.multiplier.multi)
        except (Group.DoesNotExist, GroupSettings.DoesNotExist):
            default_multi = Decimal('2.0')
        
        discount_info = {
            'has_discount': False,
            'discount_type': 'none',
            'discount_percentage': 0,
            'original_price': 0,
            'final_price': 0,
            'effective_discount_percentage': 0,
            'default_group_price': 0,
            'is_asiakas_group': self.is_asiakas_group(user),
        }
        
        # Calculate base price with default multiplier (Asiakas group)
        tax_multiplier = Decimal(1 + group_settings.tax.rate / 100)
        default_group_price = self.price * tax_multiplier * default_multi * self.multiplier
        # Round to 2 decimal places
        default_group_price = default_group_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        discount_info['default_group_price'] = float(default_group_price)
        
        # Calculate current group price
        current_group_price = self.price * tax_multiplier * base_multi * self.multiplier
        # Round to 2 decimal places
        current_group_price = current_group_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Calculate group discount percentage
        group_discount_percentage = (1 - (base_multi / default_multi)) * 100
        
        # Check if user is in Asiakas group
        is_asiakas = self.is_asiakas_group(user)
        
        if is_asiakas:
            # ASIAKAS GROUP: Product discounts and coupons allowed
            # Check coupon discount if available
            coupon_discount_percentage = 0
            coupon_price = None
            if coupon and coupon.is_valid(user) and coupon.discount:
                coupon_discount_percentage = coupon.discount
                coupon_discount_decimal = Decimal(coupon_discount_percentage) / 100
                # Coupon is always applied to default group price
                price_with_default_group = self.price * default_multi
                coupon_discounted_price = price_with_default_group * (1 - coupon_discount_decimal)
                coupon_price = coupon_discounted_price * tax_multiplier * Decimal(self.product.multiplier)
            
            # Determine which discount to use
            if self.product.discount_percentage > 0:
                # Product discount has priority
                product_discount_price = self.price * (1 - Decimal(self.product.discount_percentage) / 100)
                final_price = product_discount_price * tax_multiplier * base_multi * Decimal(self.product.multiplier)
                
                discount_info['has_discount'] = True
                discount_info['discount_type'] = 'product'
                discount_info['discount_percentage'] = self.product.discount_percentage
                discount_info['effective_discount_percentage'] = self.product.discount_percentage
                discount_info['original_price'] = round(default_group_price, 2)
                
            elif coupon_price and coupon_price < current_group_price:
                # Coupon is better than group discount
                final_price = coupon_price
                
                # Calculate effective discount percentage from default group price
                effective_discount = (1 - (coupon_price / default_group_price)) * 100
                
                discount_info['has_discount'] = True
                discount_info['discount_type'] = 'coupon'
                discount_info['discount_percentage'] = coupon_discount_percentage
                discount_info['effective_discount_percentage'] = round(effective_discount, 1)
                discount_info['original_price'] = round(default_group_price, 2)
                
            else:
                # Group discount is better or equal
                final_price = current_group_price
                
                if group_discount_percentage > 0:
                    discount_info['has_discount'] = True
                    discount_info['discount_type'] = 'group'
                    discount_info['discount_percentage'] = round(group_discount_percentage, 1)
                    discount_info['effective_discount_percentage'] = round(group_discount_percentage, 1)
                    discount_info['original_price'] = round(default_group_price, 2)
                else:
                    # No discount
                    discount_info['original_price'] = round(default_group_price, 2)
        else:
            # OTHER GROUPS: Only group discount, no product discounts, no coupons
            final_price = current_group_price
            
            if group_discount_percentage > 0:
                discount_info['has_discount'] = True
                discount_info['discount_type'] = 'group'
                discount_info['discount_percentage'] = round(group_discount_percentage, 1)
                discount_info['effective_discount_percentage'] = round(group_discount_percentage, 1)
                discount_info['original_price'] = round(default_group_price, 2)
            else:
                # No discount
                discount_info['original_price'] = round(default_group_price, 2)
        
        discount_info['final_price'] = float(final_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
        return discount_info
    
    def get_group_settings(self, user=None):
        """Get group settings for price calculations"""
        # Initialize group_settings with default values
        group_settings = GroupSettings(
            tax=Tax(rate=Decimal('0')), 
            multiplier=Multiplier(multi=Decimal('1'))
        )

        # Check if the user is authenticated
        if user and user.is_authenticated:
            if user.groups.exists():
                user_group = user.groups.first()
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

    def total_price(self, user=None, coupon=None):
        """Calculate total price with the best available discount"""
        price, discount_type = self.calculate_best_discount_price(user, coupon)
        return price

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.slug])
    
    def process_image(self):
        if self.image:
            # Open the original image
            original_img = Image.open(self.image)

            max_size = (1000, 1000)
            original_img.thumbnail(max_size)

            # Check if the image has an alpha channel (transparency)
            if original_img.mode == 'RGBA':
                # Preserve transparency when saving as WEBP
                image_mode = 'RGBA'
            else:
                # Convert to RGB if there's no alpha channel
                original_img = original_img.convert('RGB')
                image_mode = 'RGB'

            # Save the original image back to the field
            image_io = BytesIO()
            if self.image.name.lower().endswith('.png'):
                # Preserve transparency for PNG images when converting to WEBP
                original_img.save(image_io, format='WEBP', optimize=True)
                image_extension = 'webp'
            else:
                # For non-PNG images, ensure conversion to RGB before saving
                original_img.save(image_io, format='WEBP', quality=95, optimize=True)
                image_extension = 'webp'

            image_name = f"{slugify(self.name)}_{self.id}.{image_extension}"

            self.image = InMemoryUploadedFile(
                image_io,
                'ImageField',
                image_name,
                f'image/{image_extension}',
                image_io.tell(),
                None
            )

            # Create a thumbnail with the same transparency preservation
            thumbnail_size = (540, int((540 / original_img.width) * original_img.height))  # Maintain aspect ratio
            thumbnail_img = original_img.resize(thumbnail_size, resample=Image.LANCZOS)

            thumbnail_io = BytesIO()
            thumbnail_img.save(thumbnail_io, format='WEBP', quality=95, optimize=True)

            thumbnail_name = f"{slugify(self.name)}_{self.id}_thumbnail.{image_extension}"

            self.thumbnail = InMemoryUploadedFile(
                thumbnail_io,
                'ImageField',
                thumbnail_name,
                f'image/{image_extension}',
                thumbnail_io.tell(),
                None
            )

    def save(self, *args, **kwargs):
        # Check if the image has changed by comparing the current image and the new image
        if not self.pk or (self.image and self.image != self.__class__.objects.get(pk=self.pk).image):
            # Process the image only if it's a new image or the image has changed
            self.process_image()
        super().save(*args, **kwargs)

    def get_available_color_palettes(self):
        """
        Return available color palettes for this product
        """
        from django.db.models import Q
        
        palettes = {
            'color1': {'available': False, 'colors': []},
            'color2': {'available': False, 'colors': []}
        }
        
        variants = self.variants.filter(active=True)
        
        # Check Color1 - only if enabled in settings
        if self.use_color1_palette:
            color1_variants = variants.filter(
                Q(color1__isnull=False) & ~Q(color1='')
            ).values_list('color1', flat=True).distinct()
            if color1_variants:
                palettes['color1']['available'] = True
                palettes['color1']['colors'] = list(color1_variants)
        
        # Check Color2 - only if enabled in settings
        if self.use_color2_palette:
            color2_variants = variants.filter(
                Q(color2__isnull=False) & ~Q(color2='')
            ).values_list('color2', flat=True).distinct()
            if color2_variants:
                palettes['color2']['available'] = True
                palettes['color2']['colors'] = list(color2_variants)
        
        return palettes

    def get_display_palette(self):
        """
        Determine which palette to show based on settings
        """
        palettes = self.get_available_color_palettes()
        
        # If Color2 priority is selected and it's available
        if self.palette_priority == 'color2':
            if palettes['color2']['available'] and self.use_color2_palette:
                return 'color2'
            elif palettes['color1']['available'] and self.use_color1_palette:
                return 'color1'
            else:
                return None
        
        # If Color1 priority is selected and it's available
        elif self.palette_priority == 'color1':
            if palettes['color1']['available'] and self.use_color1_palette:
                return 'color1'
            elif palettes['color2']['available'] and self.use_color2_palette:
                return 'color2'
            else:
                return None
        
        return None

    def get_available_palettes_for_display(self):
        """
        Return available palettes for display in selector with priority
        """
        palettes_info = self.get_available_color_palettes()
        available_palettes = []
        
        if palettes_info['color1']['available'] and self.use_color1_palette:
            available_palettes.append('color1')
        if palettes_info['color2']['available'] and self.use_color2_palette:
            available_palettes.append('color2')
        
        # Sort according to priority
        if self.palette_priority == 'color1' and 'color1' in available_palettes:
            available_palettes.sort(key=lambda x: x != 'color1')
        elif self.palette_priority == 'color2' and 'color2' in available_palettes:
            available_palettes.sort(key=lambda x: x != 'color2')
        
        return available_palettes

    def has_colors(self):
        """
        Check if product has any colors
        """
        palettes = self.get_available_color_palettes()
        return palettes['color1']['available'] or palettes['color2']['available']
    
    def get_popularity_score(self):
        """
        Calculate popularity score based on variant orders
        Optimized method for popularity calculations
        """
        from django.db.models import Sum
        return self.variants.aggregate(
            total_orders=Sum('order_items__quantity')
        )['total_orders'] or 0
    

class ProductDocument(models.Model):
    product = models.ForeignKey('Product', related_name='documents', on_delete=models.CASCADE)
    name = models.CharField(_("Tiedoston nimi"), max_length=255, default="")
    document = models.FileField("Tiedosto", upload_to='product_documents/')

    class Meta:
        verbose_name = 'PDF Tiedosto'
        verbose_name_plural = 'PDF Tiedostot'

    def __str__(self):
        return f"Tuotteen {self.product.name} tiedosto"
    
class ProductYoutubeLink(models.Model):
    product = models.ForeignKey('Product', related_name='youtube_links', on_delete=models.CASCADE)
    name = models.CharField(_("Videon nimi"), max_length=255, default="", blank=True)
    youtube_link = models.CharField(_("YouTube koodi ilman https://youtu.be/"), max_length=255, default="")

    class Meta:
        verbose_name = _("Videolinkki")
        verbose_name_plural = _("Videolinkit")

    def __str__(self):
        return f"{self.product.name} - {self.youtube_link}"

class RelatedProduct(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='related_products')
    related_product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='related_to')

    class Meta:
        verbose_name = "Liittyvät tuotteet"
        verbose_name_plural = "Liittyvät tuotteet"

    def __str__(self):
        return f"{self.product.name} - {self.related_product.name}"

class Attribute(models.Model):
    product = models.ForeignKey(Product, related_name='attributes', on_delete=models.CASCADE)
    grain = models.CharField(max_length=2, default="", blank=True)
    family = models.CharField(max_length=200, default="", blank=True)
    purpose = models.CharField(max_length=200, default="", blank=True)
    application = models.CharField(max_length=200, default="", blank=True)
    color = models.CharField(max_length=200, default="", blank=True)
    gloss = models.CharField(max_length=200, default="", blank=True)
    sufficiency = models.CharField(max_length=200, default="", blank=True)
    voc = models.CharField(max_length=200, default="", blank=True)
    thinning = models.CharField(max_length=200, default="", blank=True)
    density = models.CharField(max_length=200, default="", blank=True)
    a_class = models.CharField(max_length=200, default="", blank=True)
    epd = models.CharField(max_length=200, default="", blank=True)
    ch2o = models.CharField(max_length=200, default="", blank=True)
    haccp = models.CharField(max_length=200, default="", blank=True)
    method = models.CharField(max_length=200, default="", blank=True)
    primer = models.CharField(max_length=200, default="", blank=True)
    ph = models.CharField(max_length=200, default="", blank=True)
    abrasion_class = models.CharField(max_length=200, default="", blank=True)

    class Meta:
        verbose_name = 'Ominaisuus'
        verbose_name_plural = 'Ominaisuudet'

class ProductImage(models.Model):
    image = models.ImageField(upload_to='products/')
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False, default=False)

    class Meta:
        verbose_name_plural = "Kuvat"

    def __str__(self):
        return f'{self.image} - {self.product}'

    def process_image(self):
        """
        Processes and converts the image to WEBP while preserving transparency (if RGBA).
        Generates a resized thumbnail as well.
        """
        # Проверяем, изменилось ли изображение
        if not self.image or self._state.adding or not self.pk:
            return

        original_img = Image.open(self.image)

        # Проверка прозрачности и конвертация для WEBP
        image_io = BytesIO()
        if original_img.mode == 'RGBA':
            original_img.save(image_io, format='WEBP', lossless=True, save_all=True)
        else:
            original_img.save(image_io, format='WEBP', quality=95, optimize=True)
        
        image_name = f"{slugify(self.product)}.webp"

        self.image = InMemoryUploadedFile(
            image_io,
            'ImageField',
            image_name,
            'image/webp',
            image_io.tell,
            None
        )

        # Генерация миниатюры
        thumbnail_size = (540, int((540 / original_img.width) * original_img.height))
        thumbnail_img = original_img.resize(thumbnail_size, resample=Image.LANCZOS)

        thumbnail_io = BytesIO()
        if original_img.mode == 'RGBA':
            thumbnail_img.save(thumbnail_io, format='WEBP', lossless=True, save_all=True)
        else:
            thumbnail_img.save(thumbnail_io, format='WEBP', quality=85, optimize=True)
        
        thumbnail_name = f"{slugify(self.product)}_thumbnail.webp"

        self.thumbnail = InMemoryUploadedFile(
            thumbnail_io,
            'ImageField',
            thumbnail_name,
            'image/webp',
            thumbnail_io.tell,
            None
        )

    def save(self, *args, **kwargs):
        # Проверка на необходимость обработки
        if self.pk:
            old_instance = ProductImage.objects.filter(pk=self.pk).first()
            if old_instance:
                # Обрабатываем изображение только если оно изменилось
                if old_instance.image != self.image:
                    self.process_image()
        else:
            self.process_image()

        super().save(*args, **kwargs)


class Variant(models.Model):
    active = models.BooleanField('Active', default=True)
    order_item = models.BooleanField('Order product', default=False)
    product = models.ForeignKey(Product, related_name='variants', null=True, blank=True, on_delete=models.CASCADE, db_index=True)
    item_code = models.CharField(max_length=100, blank=False, null=True, default='')
    item_description = models.CharField(max_length=100, blank=True, default='')
    barcode = models.BigIntegerField(blank=False, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True, null=True)
    cat_name = models.CharField(max_length=100, blank=True, default='')
    
    # Two separate color fields
    color1 = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        db_index=True, 
        default='',
        help_text="Traditional color with image files"
    )
    color2 = models.CharField(
        max_length=100, 
        null=True, 
        blank=True, 
        db_index=True, 
        default='',
        help_text="New color with RGB values"
    )
    
    size = models.CharField(max_length=100, null=True, blank=True, db_index=True, default='')
    grain = models.CharField(max_length=2, blank=True, db_index=True, default='')
    gloss = models.CharField(max_length=100, blank=True, db_index=True, default='')
    base = models.CharField(max_length=100, blank=True, db_index=True, default='')
    customs_code = models.IntegerField(null=True, blank=True, default='')
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, default='')
    
    # RGB fields for Color2
    r = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Red component (0–255)")
    g = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Green component (0–255)")
    b = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Blue component (0–255)")
    hue = models.FloatField(null=True, blank=True, help_text="Hue value (0–360 degrees)")
    
    # Image fields for Color1
    image = models.ImageField(upload_to='color_images/', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='color_thumbnails/', null=True, blank=True)

    class Meta:
        verbose_name = 'Tuotevaihtoehto'
        verbose_name_plural = 'Tuotevaihtoehdot'

    def __str__(self):
        return f"{self.product}"

    def save(self, *args, **kwargs):
        """Process images before saving if Color1 is used"""
        # Process images if Color1 exists and image was changed
        if self.color1 and self.image and (not self.pk or self._image_changed()):
            self.process_image()
        
        super().save(*args, **kwargs)

    def _image_changed(self):
        """Check if image has been changed"""
        if self.pk:
            try:
                old_instance = Variant.objects.get(pk=self.pk)
                return old_instance.image != self.image
            except Variant.DoesNotExist:
                return True
        return True

    def process_image(self):
        """Process and optimize color images for Color1"""
        if not self.image:
            return

        # Open the original image
        original_img = Image.open(self.image)

        # Resize main image
        max_size = (400, 300)
        original_img.thumbnail(max_size, Image.LANCZOS)

        # Determine format and process accordingly
        image_io = BytesIO()
        if original_img.mode == 'RGBA':
            # Preserve transparency for PNG/WEBP
            original_img.save(image_io, format='WEBP', lossless=True)
            content_type = 'image/webp'
            extension = 'webp'
        else:
            # Convert to RGB for JPEG/WEBP
            if original_img.mode != 'RGB':
                original_img = original_img.convert('RGB')
            original_img.save(image_io, format='WEBP', quality=85)
            content_type = 'image/webp'
            extension = 'webp'

        # Generate filename
        color_slug = slugify(self.color1) if self.color1 else 'color'
        image_name = f"{color_slug}_{self.item_code or 'variant'}.{extension}"

        # Save processed image
        self.image = InMemoryUploadedFile(
            image_io,
            'ImageField',
            image_name,
            content_type,
            image_io.tell(),
            None
        )

        # Create thumbnail
        thumbnail_size = (64, 48)
        thumbnail_img = original_img.copy()
        thumbnail_img.thumbnail(thumbnail_size, Image.LANCZOS)

        thumbnail_io = BytesIO()
        if original_img.mode == 'RGBA':
            thumbnail_img.save(thumbnail_io, format='WEBP', lossless=True)
        else:
            thumbnail_img.save(thumbnail_io, format='WEBP', quality=80)

        thumbnail_name = f"{color_slug}_{self.item_code or 'variant'}_thumbnail.{extension}"

        self.thumbnail = InMemoryUploadedFile(
            thumbnail_io,
            'ImageField',
            thumbnail_name,
            content_type,
            thumbnail_io.tell(),
            None
        )

    @property
    def color(self):
        """Computed property that returns color1 or color2"""
        return self.color1 or self.color2 or ''
    
    @color.setter
    def color(self, value):
        """Setter for color - determines where to store based on context"""
        # This is read-only for display purposes
        # Actual saving happens through color1 or color2 fields
        pass

    def get_color_type(self):
        """Return color type based on which color field is populated"""
        if self.color1:
            return 'color1'
        elif self.color2:
            return 'color2'
        return ''

    def get_color_name(self):
        """Return color name from appropriate field"""
        return self.color1 or self.color2 or ''

    def get_display_color(self):
        """Get color for display purposes"""
        return {
            'name': self.get_color_name(),
            'type': self.get_color_type(),
            'r': self.r,
            'g': self.g,
            'b': self.b,
            'image': self.image
        }

    def get_active_color(self):
        """Get the active color information (Color1 has priority over Color2)"""
        color_name = self.get_color_name()
        color_type = self.get_color_type()
        
        if color_type == 'color1':
            return {
                'type': 'color1',
                'name': color_name,
                'has_image': bool(self.image),
                'image_url': self.image.url if self.image else None,
                'thumbnail_url': self.thumbnail.url if self.thumbnail else None
            }
        elif color_type == 'color2':
            return {
                'type': 'color2',
                'name': color_name,
                'has_rgb': all([self.r is not None, self.g is not None, self.b is not None]),
                'rgb': (self.r, self.g, self.b),
                'hue': self.hue,
                'css_rgb': f"rgb({self.r}, {self.g}, {self.b})" if all([self.r is not None, self.g is not None, self.b is not None]) else None
            }
        else:
            return {
                'type': 'none',
                'name': ''
            }

    def get_image_url(self):
        """Get image URL for Color1, fallback to product image"""
        if self.color1 and self.image and hasattr(self.image, 'url'):
            return self.image.url
        elif self.product and self.product.image:
            return self.product.image.url
        return ''

    def get_thumbnail_url(self):
        """Get thumbnail URL for Color1, fallback to product thumbnail"""
        if self.color1 and self.thumbnail and hasattr(self.thumbnail, 'url'):
            return self.thumbnail.url
        elif self.product and hasattr(self.product, 'thumbnail') and self.product.thumbnail:
            return self.product.thumbnail.url
        return self.get_image_url()

    def get_rgb_color(self):
        """Get RGB color for Color2, returns CSS string if available"""
        if self.color2 and all([self.r is not None, self.g is not None, self.b is not None]):
            return f"rgb({self.r}, {self.g}, {self.b})"
        return None

    def has_color(self):
        """Check if variant has any color data"""
        return bool(self.color1 or self.color2)

    def clean(self):
        """Validation to ensure proper field usage"""
        from django.core.exceptions import ValidationError
        
        # Color1 and Color2 should not both be set (though technically possible)
        if self.color1 and self.color2:
            raise ValidationError("Only one of Color1 or Color2 should be set, not both.")
            
        # For Color1, image is recommended but not required
        # For Color2, RGB values are recommended but not required

    def get_cart_data(self):
        """Get variant data for cart serialization"""
        color_type = self.get_color_type()
        color_name = self.get_color_name()
        
        cart_data = {
            'id': self.id,
            'item_code': self.item_code,
            'size': self.size,
            'grain': self.grain,
            'gloss': self.gloss,
            'base': self.base,
            'order_item': self.order_item,
            'color': color_name,
            'color_type': color_type,  # Add color type information
        }
        
        # Add color-specific data
        if color_type == 'color1':
            cart_data['thumbnail_url'] = self.get_thumbnail_url()
        elif color_type == 'color2':
            cart_data['r'] = self.r
            cart_data['g'] = self.g
            cart_data['b'] = self.b
        
        return cart_data

    def get_cart_display_data(self):
        """Get color data specifically for cart display"""
        color_type = self.get_color_type()
        color_name = self.get_color_name()
        
        if color_type == 'color1':
            return {
                'color': color_name,
                'color_type': 'color1',
                'thumbnail_url': self.get_thumbnail_url(),
                'r': None,
                'g': None,
                'b': None
            }
        elif color_type == 'color2':
            return {
                'color': color_name,
                'color_type': 'color2',
                'thumbnail_url': None,
                'r': self.r,
                'g': self.g,
                'b': self.b
            }
        else:
            return {
                'color': '',
                'color_type': '',
                'thumbnail_url': None,
                'r': None,
                'g': None,
                'b': None
            }

    def get_group_settings(self, user=None):
        """Get group settings for price calculations"""
        # Initialize group_settings with default values
        group_settings = GroupSettings(
            tax=Tax(rate=Decimal('0')), 
            multiplier=Multiplier(multi=Decimal('1'))
        )

        # Check if the user is authenticated
        if user and user.is_authenticated:
            if user.groups.exists():
                user_group = user.groups.first()
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
        if not user or not user.is_authenticated:
            return True  # Default to Asiakas for anonymous users
        
        if user.groups.exists():
            user_group = user.groups.first()
            return user_group.name == "Asiakas"
        else:
            return True  # No group assigned, default to Asiakas

    def calculate_best_discount_price(self, user=None, coupon=None):
        """
        Calculate price with the best available discount (only one discount applied)
        """
        group_settings = self.get_group_settings(user)
        base_multi = Decimal(group_settings.multiplier.multi)

        # Use the appropriate tax and multiplier values
        tax_multiplier = Decimal(1 + group_settings.tax.rate / 100)

        base_price = self.price
        
        # Check if user is in Asiakas group
        is_asiakas = self.is_asiakas_group(user)
        
        if is_asiakas:
            # ASIAKAS GROUP LOGIC: Product discounts and coupons allowed
            # Calculate all possible discounted prices
            prices = []
            
            # 1. Product discount (always has highest priority)
            if self.product.discount_percentage > 0:
                product_discount_percentage = Decimal(self.product.discount_percentage) / 100
                product_discounted_price = base_price * (1 - product_discount_percentage)
                product_final_price = product_discounted_price * tax_multiplier * base_multi * Decimal(self.product.multiplier)
                # Round to 2 decimal places
                product_final_price = product_final_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                prices.append(('product', product_final_price))
            
            # 2. Group discount price (always available)
            group_final_price = base_price * tax_multiplier * base_multi * Decimal(self.product.multiplier)
            # Round to 2 decimal places
            group_final_price = group_final_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            prices.append(('group', group_final_price))
            
            # 3. Coupon discount (only if valid and NO product discount exists)
            coupon_discount_percentage = 0
            if (coupon and coupon.is_valid(user) and coupon.discount and 
                self.product.discount_percentage == 0):
                
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
                coupon_final_price = coupon_discounted_price * tax_multiplier * Decimal(self.product.multiplier)
                # Round to 2 decimal places
                coupon_final_price = coupon_final_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                # Only add coupon price if it's better than current group price
                if coupon_final_price < group_final_price:
                    prices.append(('coupon', coupon_final_price))
            
            # Return the price with the highest discount (lowest price)
            if prices:
                best_price = min(prices, key=lambda x: x[1])
                return best_price[1], best_price[0]
            else:
                # Fallback to group price
                return group_final_price, 'group'
        
        else:
            # OTHER GROUPS LOGIC: Only group discount, no product discounts, no coupons
            # Only apply group discount for other groups
            group_final_price = base_price * tax_multiplier * base_multi * Decimal(self.product.multiplier)
            # Round to 2 decimal places
            group_final_price = group_final_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            return group_final_price, 'group'

    def get_discount_info(self, user=None, coupon=None):
        """
        Get detailed discount information for display
        """
        group_settings = self.get_group_settings(user)
        base_multi = Decimal(group_settings.multiplier.multi)
        
        # Get default group multiplier for comparison
        default_group_name = "Asiakas"
        try:
            default_group = Group.objects.get(name=default_group_name)
            default_group_settings = GroupSettings.objects.get(group=default_group)
            default_multi = Decimal(default_group_settings.multiplier.multi)
        except (Group.DoesNotExist, GroupSettings.DoesNotExist):
            default_multi = Decimal('2.0')
        
        discount_info = {
            'has_discount': False,
            'discount_type': 'none',
            'discount_percentage': 0,
            'original_price': 0,
            'final_price': 0,
            'effective_discount_percentage': 0,
            'default_group_price': 0,
            'is_asiakas_group': self.is_asiakas_group(user),
        }
        
        # Calculate base price with default multiplier (Asiakas group)
        tax_multiplier = Decimal(1 + group_settings.tax.rate / 100)
        default_group_price = self.price * tax_multiplier * default_multi * self.multiplier
        # Round to 2 decimal places
        default_group_price = default_group_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        discount_info['default_group_price'] = float(default_group_price)
        
        # Calculate current group price
        current_group_price = self.price * tax_multiplier * base_multi * self.multiplier
        # Round to 2 decimal places
        current_group_price = current_group_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Calculate group discount percentage
        group_discount_percentage = (1 - (base_multi / default_multi)) * 100
        
        # Check if user is in Asiakas group
        is_asiakas = self.is_asiakas_group(user)
        
        if is_asiakas:
            # ASIAKAS GROUP: Product discounts and coupons allowed
            # Check coupon discount if available
            coupon_discount_percentage = 0
            coupon_price = None
            if coupon and coupon.is_valid(user) and coupon.discount:
                coupon_discount_percentage = coupon.discount
                coupon_discount_decimal = Decimal(coupon_discount_percentage) / 100
                # Coupon is always applied to default group price
                price_with_default_group = self.price * default_multi
                coupon_discounted_price = price_with_default_group * (1 - coupon_discount_decimal)
                coupon_price = coupon_discounted_price * tax_multiplier * Decimal(self.product.multiplier)
            
            # Determine which discount to use
            if self.product.discount_percentage > 0:
                # Product discount has priority
                product_discount_price = self.price * (1 - Decimal(self.product.discount_percentage) / 100)
                final_price = product_discount_price * tax_multiplier * base_multi * Decimal(self.product.multiplier)
                
                discount_info['has_discount'] = True
                discount_info['discount_type'] = 'product'
                discount_info['discount_percentage'] = self.product.discount_percentage
                discount_info['effective_discount_percentage'] = self.product.discount_percentage
                discount_info['original_price'] = round(default_group_price, 2)
                
            elif coupon_price and coupon_price < current_group_price:
                # Coupon is better than group discount
                final_price = coupon_price
                
                # Calculate effective discount percentage from default group price
                effective_discount = (1 - (coupon_price / default_group_price)) * 100
                
                discount_info['has_discount'] = True
                discount_info['discount_type'] = 'coupon'
                discount_info['discount_percentage'] = coupon_discount_percentage
                discount_info['effective_discount_percentage'] = round(effective_discount, 1)
                discount_info['original_price'] = round(default_group_price, 2)
                
            else:
                # Group discount is better or equal
                final_price = current_group_price
                
                if group_discount_percentage > 0:
                    discount_info['has_discount'] = True
                    discount_info['discount_type'] = 'group'
                    discount_info['discount_percentage'] = round(group_discount_percentage, 1)
                    discount_info['effective_discount_percentage'] = round(group_discount_percentage, 1)
                    discount_info['original_price'] = round(default_group_price, 2)
                else:
                    # No discount
                    discount_info['original_price'] = round(default_group_price, 2)
        else:
            # OTHER GROUPS: Only group discount, no product discounts, no coupons
            final_price = current_group_price
            
            if group_discount_percentage > 0:
                discount_info['has_discount'] = True
                discount_info['discount_type'] = 'group'
                discount_info['discount_percentage'] = round(group_discount_percentage, 1)
                discount_info['effective_discount_percentage'] = round(group_discount_percentage, 1)
                discount_info['original_price'] = round(default_group_price, 2)
            else:
                # No discount
                discount_info['original_price'] = round(default_group_price, 2)
        
        discount_info['final_price'] = float(final_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
        return discount_info

    def total_price(self, user=None, coupon=None):
        """Calculate total price with the best available discount"""
        price, discount_type = self.calculate_best_discount_price(user, coupon)
        return price

    def get_price_without_discount(self, user=None):
        """Calculate price without any discount but with tax and multiplier"""
        group_settings = self.get_group_settings(user)

        # Use the appropriate tax and multiplier values
        tax_multiplier = Decimal(1 + group_settings.tax.rate / 100)
        multi = Decimal(group_settings.multiplier.multi)

        # Calculate price without discount
        return round(self.price * tax_multiplier * multi, 2)
    

class ProductMaterialCalculatorPackage(models.Model):
    product = models.ForeignKey(
        Product,
        related_name='material_calculator_packages',
        on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name='Tuote'
    )
    variant = models.ForeignKey(
        Variant,
        related_name='material_calculator_packages',
        on_delete=models.CASCADE,
        db_constraint=False,
        verbose_name='Laskennassa mukana oleva tuotevaihtoehto'
    )
    active = models.BooleanField(default=True, verbose_name='Mukana laskurissa')
    label = models.CharField(
        max_length=100,
        blank=True,
        default='',
        verbose_name='Pakkauskoko / näytettävä teksti',
        help_text='Esimerkiksi 0,75 l, 2,5 l tai 20 kg. Jos tyhjä, käytetään määrää ja yksikköä.'
    )
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        validators=[MinValueValidator(Decimal('0.001'))],
        verbose_name='Tuotteen määrä pakkauksessa'
    )
    unit = models.CharField(
        max_length=2,
        choices=MATERIAL_CALCULATOR_PACKAGE_UNITS,
        verbose_name='Pakkausyksikkö'
    )
    order = models.PositiveIntegerField(default=0, verbose_name='Järjestys')

    class Meta:
        ordering = ('order', 'amount', 'id')
        verbose_name = 'Menekkilaskurin pakkaus'
        verbose_name_plural = 'Menekkilaskurin pakkaukset'

    def __str__(self):
        return f'{self.product} - {self.display_label}'

    @property
    def display_label(self):
        if self.label:
            return self.label
        amount = self.amount.normalize()
        return f'{amount} {self.unit}'

    def clean(self):
        super().clean()
        if self.variant_id and self.product_id and self.variant.product_id != self.product_id:
            raise ValidationError({
                'variant': 'Tuotevaihtoehdon pitää kuulua tähän tuotteeseen.'
            })


class Coupon(models.Model):
    active = models.BooleanField('Aktiivinen', default=True)
    code = models.CharField('Koodi', max_length=50, unique=True)
    discount = models.IntegerField('Alennusprosentti', blank=True, null=True)
    amount = models.DecimalField('Summa', max_digits=10, decimal_places=2, blank=True, null=True)
    min_purchase = models.DecimalField('Minimiostos', max_digits=10, decimal_places=2, null=True, blank=True)
    free_shipping = models.BooleanField('Ilmainen toimitus', default=False)
    start_date = models.DateTimeField('Alkamispäivä', default=timezone.now)
    end_date = models.DateTimeField('Päättymispäivä', blank=True, null=True)
    single_use = models.BooleanField('Kertakäyttöinen', default=False)
    used_by = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, verbose_name='Käyttäjät jotka ovat käyttäneet')
    used_by_anonymous = models.BooleanField('Käytetty anonyymisti', default=False)

    def __str__(self):
        return self.code
    
    class Meta:
        verbose_name = 'Kuponki'
        verbose_name_plural = 'Kupongit'

    def is_valid(self, user=None):
        """
        Check if the coupon is currently valid based on active status, date range, and usage.
        """
        now = timezone.now()
        valid = (
            self.active and 
            self.start_date <= now and 
            (self.end_date is None or self.end_date >= now) and
            (self.discount or self.amount or self.free_shipping)
        )
        
        if not valid:
            return False
            
        if self.single_use:
            # For anonymous users check used_by_anonymous flag
            if user is None or user.is_anonymous:
                return not self.used_by_anonymous
            else:
                # For authenticated users check if they already used the coupon
                return not self.used_by.filter(id=user.id).exists()
                
        return True

    def mark_as_used(self, user=None):
        """
        Mark coupon as used by a user or anonymously
        """
        if self.single_use:
            if user is None or user.is_anonymous:
                self.used_by_anonymous = True
            else:
                self.used_by.add(user)
            self.save()

class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    active = models.BooleanField(default=False)
    user = models.ForeignKey(CustomUser, related_name='users_reviews', on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey('order.Order', related_name='reviews', on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=130, blank=False)
    rating = models.PositiveIntegerField(default=0, validators=[MinValueValidator(1), MaxValueValidator(5)])
    image = models.ImageField(upload_to='rating_photos/', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='rating_thumbnails/', blank=True)
    title = models.CharField(max_length=200, blank=True)
    text = models.TextField(blank=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Arvostelu'
        verbose_name_plural = 'Arvostelut'

    def get_rating_percent(self):
        return self.rating * 20
    
    def calculate_average_rating(self):
        average_rating = Review.objects.filter(product=self.product, active=True).aggregate(avg_rating=Avg('rating'))['avg_rating']
        
        if average_rating is None:
            return 0

        average_rating_percent = round((average_rating / 5) * 100, 2)
        return average_rating_percent

    def average_rating_value(self):
        average_rating = self.calculate_average_rating()
        if average_rating is not None:
            return round(average_rating / 20, 2)
        else:
            return 0
        
    def process_image(self):
        if self.image:
            # Open the original image
            original_img = Image.open(self.image)

            max_size = (1024, 1024)
            original_img.thumbnail(max_size)

            # Save the original image back to the field
            image_io = BytesIO()
            if self.image.name.lower().endswith('.png'):
                # Preserve transparency for PNG images
                original_img.save(image_io, format='PNG', optimize=True)
                image_extension = 'png'
            else:
                # Convert to RGB for JPEG images
                if original_img.mode == 'RGBA':
                    original_img = original_img.convert('RGB')
                original_img.save(image_io, format='JPEG', quality=95)  # JPEG quality 95
                image_extension = 'jpg'

            image_name = f"{slugify(self.name)}.{image_extension}"

            self.image = InMemoryUploadedFile(
                image_io,
                'ImageField',
                image_name,
                f'image/{image_extension}',
                image_io.tell,
                None
            )

            # Create a thumbnail
            thumbnail_size = (120, int((120 / original_img.width) * original_img.height))  # Maintain aspect ratio
            thumbnail_img = original_img.resize(thumbnail_size, resample=Image.LANCZOS)  # Use Lanczos resampling for better quality

            # Save the thumbnail image
            thumbnail_io = BytesIO()
            if image_extension == 'png':
                # Preserve transparency for PNG images
                thumbnail_img.save(thumbnail_io, format='PNG', optimize=True)
            else:
                thumbnail_img.save(thumbnail_io, format='JPEG', quality=95)  # JPEG quality 95
            
            thumbnail_name = f"{slugify(self.name)}_thumbnail.{image_extension}"

            self.thumbnail = InMemoryUploadedFile(
                thumbnail_io,
                'ImageField',
                thumbnail_name,
                f'image/{image_extension}',
                thumbnail_io.tell,
                None
            )
        
    def save(self, *args, **kwargs):
        self.process_image()
        super().save(*args, **kwargs)

class GroupSettings(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    tax = models.ForeignKey(Tax, on_delete=models.SET_NULL, null=True, blank=True)
    multiplier = models.ForeignKey(Multiplier, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Ryhmä'
        verbose_name_plural = 'Ryhmät'

    def __str__(self):
        return f"Ryhmäasetukset: {self.group}"

class Contact(models.Model):
    email = models.EmailField(blank=True)
    title = models.CharField(max_length=130)
    text = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Yhteydenotto'

class RecentProductView(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=False, blank=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']
        verbose_name = 'Viimeksi katsottu'
        verbose_name_plural = 'Viimeksi katsotut'
