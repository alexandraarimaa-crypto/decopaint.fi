from django.db import models
from django.urls import reverse
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.core.validators import MaxValueValidator, MinValueValidator 
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from django.contrib.auth.models import Group
from users.models import CustomUser
from decimal import Decimal
from tinymce.models import HTMLField
from django.utils.translation import gettext_lazy as _
from django.db.models import Avg
from datetime import datetime
from django.utils import timezone

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

    class Meta:
        verbose_name = 'Kaupan asetukset'
        verbose_name_plural = 'Kaupan asetukset'

    def __str__(self):
        return f'Kaupan asetukset'

class Category(models.Model):
    active = models.BooleanField(default=True)
    name = models.CharField(max_length=200, db_index=True, default='')
    slug = models.SlugField(max_length=200, unique=True)
    bg_image = models.ImageField(upload_to='category_images', blank=True, null=True)
    info = models.TextField(blank=True, default='')

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

            max_size = (1920, 1080)
            original_img.thumbnail(max_size)

            # Save the original image back to the field
            image_io = BytesIO()
            if self.bg_image.name.lower().endswith('.png'):
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
            if not self.bg_image.name:
                # Generate a unique filename based on the current date and time
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                image_name = f"{timestamp}_{self.id}.{image_extension}"
            else:
                # Keep the original filename
                image_name = self.bg_image.name

            self.bg_image = InMemoryUploadedFile(
                image_io,
                'ImageField',
                image_name,
                f'image/{image_extension}',
                image_io.tell,
                None
            )

    def save(self, *args, **kwargs):
        #self.process_image()  # Обработка изображения
        super().save(*args, **kwargs)  # Сохранение
    
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
        validators=[MinValueValidator(limit_value=1.00)]
    )
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    sku = models.CharField(max_length=200, db_index=True, blank=True, default='')
    image = models.ImageField(upload_to='products/', blank=True)
    thumbnail = models.ImageField(upload_to='thumbnails/', blank=True)
    description = HTMLField(blank=True, default='')
    tech_info = HTMLField(blank=True, default='')
    properties = HTMLField(blank=True, default='')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField(Tag, related_name='products', blank=True)

    class Meta:
        ordering = ('name',)
        index_together = (('id', 'slug'),)
        verbose_name = 'Tuote'
        verbose_name_plural = 'Tuotteet'

    def __str__(self):
        return self.name
    
    def decrease_stock_quantity(self, quantity):
        self.stock -= quantity
        self.save()

    def increase_stock_quantity(self, quantity):
        self.stock += quantity
        self.save()
    
    def total_price(self, user=None):
        # Initialize group_settings with default values
        group_settings = GroupSettings(tax=Tax(rate=Decimal('0')), multiplier=Multiplier(multi=Decimal('1')))

        # Check if the user is authenticated
        if user and user.is_authenticated:
            # If authenticated, get the user's group settings
            if user.groups.exists():
                # If authenticated and has groups, get the first group
                user_group = user.groups.first()
                try:
                    group_settings = GroupSettings.objects.get(group=user_group)
                except GroupSettings.DoesNotExist:
                    # Handle the case where the group settings do not exist for the user's group
                    pass
            else:
                default_group_name = "Asiakas"
                try:
                    user_group = Group.objects.get(name=default_group_name)
                    group_settings = GroupSettings.objects.get(group=user_group)
                except Group.DoesNotExist or GroupSettings.DoesNotExist:
                    # Handle the case where the default group or settings do not exist
                    pass
        else:
            # If not authenticated, use the default group settings for "Asiakas"
            default_group_name = "Asiakas"
            try:
                user_group = Group.objects.get(name=default_group_name)
                group_settings = GroupSettings.objects.get(group=user_group)
            except Group.DoesNotExist or GroupSettings.DoesNotExist:
                # Handle the case where the default group or settings do not exist
                pass

        # Use the appropriate tax and multiplier values
        tax_multiplier = 1 + group_settings.tax.rate / 100
        multi = group_settings.multiplier.multi

        # Calculate the total price
        return round(self.price * tax_multiplier * multi * self.multiplier, 2)

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.category.slug, self.slug])
    
    def process_image(self):
        if self.image:
            # Open the original image
            original_img = Image.open(self.image)

            max_size = (1000, 1000)
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

            image_name = f"{slugify(self.name)}_{self.id}.{image_extension}"

            self.image = InMemoryUploadedFile(
                image_io,
                'ImageField',
                image_name,
                f'image/{image_extension}',
                image_io.tell,
                None
            )

            # Create a thumbnail
            thumbnail_size = (540, int((540 / original_img.width) * original_img.height))  # Maintain aspect ratio
            thumbnail_img = original_img.resize(thumbnail_size, resample=Image.LANCZOS)  # Use Lanczos resampling for better quality

            # Save the thumbnail image
            thumbnail_io = BytesIO()
            if image_extension == 'png':
                # Preserve transparency for PNG images
                thumbnail_img.save(thumbnail_io, format='PNG', optimize=True)
            else:
                thumbnail_img.save(thumbnail_io, format='JPEG', quality=95)  # JPEG quality 95
            
            thumbnail_name = f"{slugify(self.name)}_{self.id}_thumbnail.{image_extension}"

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
        if self.image:
            original_img = Image.open(self.image)

            max_size = (1000, 1000)
            original_img.thumbnail(max_size)

            image_io = BytesIO()
            if self.image.name.lower().endswith('.png'):
                original_img.save(image_io, format='PNG', optimize=True)
                image_extension = 'png'
            else:
                if original_img.mode == 'RGBA':
                    original_img = original_img.convert('RGB')
                original_img.save(image_io, format='JPEG', quality=95)
                image_extension = 'jpg'

            image_name = f"{slugify(self.product)}.jpg"

            self.image = InMemoryUploadedFile(
                image_io,
                'ImageField',
                image_name,
                f'image/{image_extension}',
                image_io.tell,
                None
            )

            thumbnail_size = (540, int((540 / original_img.width) * original_img.height))
            thumbnail_img = original_img.resize(thumbnail_size, resample=Image.LANCZOS)

            thumbnail_io = BytesIO()
            if image_extension == 'png':
                thumbnail_img.save(thumbnail_io, format='PNG', optimize=True)
            else:
                thumbnail_img.save(thumbnail_io, format='JPEG', quality=95)
            
            thumbnail_name = f"{slugify(self.product)}_thumbnail.jpg"

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

class Variant(models.Model):
    active = models.BooleanField('Aktiivinen', default=True)
    order_item = models.BooleanField('Tilaustuote', default=False, blank=False)
    product = models.ForeignKey(Product, related_name='variants', null=True, blank=True, on_delete=models.CASCADE, db_index=True)
    item_code = models.CharField(max_length=100, blank=False, null=True, default='')
    item_description = models.CharField(max_length=100, blank=True, default='')
    barcode = models.BigIntegerField(blank=False, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, db_index=True, null=True)
    cat_name = models.CharField(max_length=100, blank=True, default='')
    color = models.CharField(max_length=100, blank=True, db_index=True, default='')
    size = models.CharField(max_length=100, blank=True, db_index=True, default='')
    grain = models.CharField(max_length=2, blank=True, db_index=True, default='')
    gloss = models.CharField(max_length=100, blank=True, db_index=True, default='')
    base = models.CharField(max_length=100, blank=True, db_index=True, default='')
    customs_code = models.IntegerField(null=True, blank=True, default='')
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, default='')
    image = models.ImageField(upload_to='color_images/', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='color_thumbnails/', blank=True)

    class Meta:
        verbose_name = 'Tuotevaihtoehto'
        verbose_name_plural = 'Tuotevaihtoehdot'

    def __str__(self):
        return f"{self.product}"
    
    def get_image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.product.image.url
        else:
            return self.product.image.url if self.product.image else 'https://www.mystore.com/default_image.jpg'
    
    def process_image(self):
        if self.image:
            # Open the original image
            original_img = Image.open(self.image)

            max_size = (400, 300)
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

            image_name = f"{slugify(self.image.name)}_{self.id}.{image_extension}"

            self.image = InMemoryUploadedFile(
                image_io,
                'ImageField',
                image_name,
                f'image/{image_extension}',
                image_io.tell,
                None
            )

            # Create a thumbnail
            thumbnail_size = (64, int((64 / original_img.width) * original_img.height))  # Maintain aspect ratio
            thumbnail_img = original_img.resize(thumbnail_size, resample=Image.LANCZOS)  # Use Lanczos resampling for better quality

            # Save the thumbnail image
            thumbnail_io = BytesIO()
            if image_extension == 'png':
                # Preserve transparency for PNG images
                thumbnail_img.save(thumbnail_io, format='PNG', optimize=True)
            else:
                thumbnail_img.save(thumbnail_io, format='JPEG', quality=95)  # JPEG quality 95
            
            thumbnail_name = f"{slugify(self.image.name)}_{self.id}_thumbnail.{image_extension}"

            self.thumbnail = InMemoryUploadedFile(
                thumbnail_io,
                'ImageField',
                thumbnail_name,
                f'image/{image_extension}',
                thumbnail_io.tell,
                None
            )

    def total_price(self, user=None):
        # Initialize group_settings with default values
        group_settings = GroupSettings(tax=Tax(rate=Decimal('0')), multiplier=Multiplier(multi=Decimal('1')))

        # Check if the user is authenticated
        if user and user.is_authenticated:
            # If authenticated, get the user's group settings
            if user.groups.exists():
                # If authenticated and has groups, get the first group
                user_group = user.groups.first()
                try:
                    group_settings = GroupSettings.objects.get(group=user_group)
                except GroupSettings.DoesNotExist:
                    # Handle the case where the group settings do not exist for the user's group
                    pass
            else:
                default_group_name = "Asiakas"
                try:
                    user_group = Group.objects.get(name=default_group_name)
                    group_settings = GroupSettings.objects.get(group=user_group)
                except Group.DoesNotExist or GroupSettings.DoesNotExist:
                    # Handle the case where the default group or settings do not exist
                    pass
        else:
            # If not authenticated, use the default group settings for "Asiakas"
            default_group_name = "Asiakas"
            try:
                user_group = Group.objects.get(name=default_group_name)
                group_settings = GroupSettings.objects.get(group=user_group)
            except Group.DoesNotExist or GroupSettings.DoesNotExist:
                # Handle the case where the default group or settings do not exist
                pass

        # Use the appropriate tax and multiplier values
        tax_multiplier = 1 + group_settings.tax.rate / 100
        multi = group_settings.multiplier.multi

        # Calculate the total price
        return round(self.price * tax_multiplier * multi * self.product.multiplier, 2)
    
    def save(self, *args, **kwargs):
        self.process_image()
        super().save(*args, **kwargs)

class Coupon(models.Model):
    active = models.BooleanField('Aktiivinen', default=True)
    code = models.CharField('Koodi', max_length=50, unique=True)
    discount = models.IntegerField('Alennusprosentti', blank=True, null=True)
    amount = models.DecimalField('Summa', max_digits=10, decimal_places=2, blank=True, null=True)
    min_purchase = models.DecimalField('Minimiostos', max_digits=10, decimal_places=2, null=True, blank=True)
    free_shipping = models.BooleanField('Ilmainen toimitus', default=False)
    start_date = models.DateTimeField('Alkamispäivä', default=timezone.now)
    end_date = models.DateTimeField('Päättymispäivä', blank=True, null=True)

    def __str__(self):
        return self.code
    
    class Meta:
        verbose_name = 'Kuponki'
        verbose_name_plural = 'Kupongit'

    def is_valid(self):
        """
        Check if the coupon is currently valid based on active status and date range.
        """
        now = timezone.now()
        if self.active and self.start_date <= now and (self.end_date is None or self.end_date >= now):
            if self.discount or self.amount or self.free_shipping:
                return True
        return False

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
