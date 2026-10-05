from django.db import models
from tinymce.models import HTMLField
from PIL import Image
from django.utils.text import slugify
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

class Service(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, null=True, blank=True)
    content = HTMLField('Sisältö', blank=False)
    image = models.ImageField(upload_to='services_images/', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='services_images/thumbnails/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # SEO fields
    meta_title = models.CharField(max_length=200, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

    def process_image(self):
        if self.image:
            # Open the original image
            original_img = Image.open(self.image)
            
            # Convert to RGB if necessary (e.g. for PNG with transparency being saved as JPEG/WEBP without alpha)
            # However, logic below handles WEBP with transparency for PNGs.
            
            # Standardize logic from blog/models.py
            image_io = BytesIO()
            if self.image.name.lower().endswith('.png'):
                original_img.save(image_io, format='WEBP', optimize=True)
                image_extension = 'webp'
            else:
                if original_img.mode == 'RGBA':
                    original_img = original_img.convert('RGB')
                original_img.save(image_io, format='WEBP', quality=95)
                image_extension = 'webp'

            image_name = f"{slugify(self.title)}_{self.id}.{image_extension}"

            self.image = InMemoryUploadedFile(
                image_io,
                'ImageField',
                image_name,
                f'image/{image_extension}',
                image_io.tell,
                None
            )

            # Create a thumbnail
            thumbnail_size = (540, int((540 / original_img.width) * original_img.height))
            thumbnail_img = original_img.resize(thumbnail_size, resample=Image.LANCZOS)

            thumbnail_io = BytesIO()
            if image_extension == 'webp':
                thumbnail_img.save(thumbnail_io, format='WEBP', optimize=True)
            else:
                thumbnail_img.save(thumbnail_io, format='WEBP', quality=95)
            
            thumbnail_name = f"{slugify(self.title)}_{self.id}_thumbnail.{image_extension}"

            self.thumbnail = InMemoryUploadedFile(
                thumbnail_io,
                'ImageField',
                thumbnail_name,
                f'image/{image_extension}',
                thumbnail_io.tell,
                None
            )
    
    def save(self, *args, **kwargs):
        # We need an ID for filename generation, so save first if no ID
        if not self.pk:
            super().save(*args, **kwargs)
            
        self.process_image()
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('services:service_detail', kwargs={'slug': self.slug})

    class Meta:
        verbose_name = 'Palvelu'
        verbose_name_plural = 'Palvelut'

class QuoteRequest(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='quote_requests', verbose_name='Palvelu')
    name = models.CharField(max_length=100, verbose_name='Nimi')
    email = models.EmailField(verbose_name='Sähköposti')
    phone = models.CharField(max_length=20, verbose_name='Puhelin')
    message = models.TextField(verbose_name='Viesti')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Luotu')

    def __str__(self):
        return f"{self.name} - {self.service.title}"

    class Meta:
        verbose_name = 'Tarjouspyyntö'
        verbose_name_plural = 'Tarjouspyynnöt'
        ordering = ['-created_at']

class QuoteRequestFile(models.Model):
    quote_request = models.ForeignKey(QuoteRequest, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='quote_requests/', verbose_name='Tiedosto')
    
    def __str__(self):
        return self.file.name.split('/')[-1]

class ServiceAdditionalImage(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='additional_images')
    image = models.ImageField(upload_to='services_images/additional/', null=True, blank=True)

    def __str__(self):
        return f"Image for {self.service.title}"

    def process_image(self):
        if self.image:
            # Open the original image
            original_img = Image.open(self.image)

            # Set the maximum size for the larger side to 1600px
            max_size = (1600, 1600)

            # Resize the image so that the larger side is no more than 800px while maintaining aspect ratio
            original_img.thumbnail(max_size, Image.LANCZOS)

            # Save the resized image to a byte stream
            image_io = BytesIO()
            if self.image.name.lower().endswith('.png'):
                # Preserve transparency for PNG images
                original_img.save(image_io, format='WEBP', optimize=True)
                image_extension = 'webp'
            else:
                # Convert to RGB for non-PNG images
                if original_img.mode == 'RGBA':
                    original_img = original_img.convert('RGB')
                original_img.save(image_io, format='WEBP', quality=95)
                image_extension = 'webp'

            # Create a new filename based on the service title and image ID
            image_name = f"{slugify(self.service.title)}_{self.id}_additional.{image_extension}"

            # Save the processed image back to the image field
            self.image = InMemoryUploadedFile(
                image_io,
                'ImageField',
                image_name,
                f'image/{image_extension}',
                image_io.tell,
                None
            )

    def save(self, *args, **kwargs):
        self.process_image()  # Process the image before saving
        super().save(*args, **kwargs)
