from django.db import models
from tinymce.models import HTMLField
from PIL import Image
from django.utils.text import slugify
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
from shop.models import Product

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Blogi kategoria'
        verbose_name_plural = 'Blogi kategoriat'

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, null=True, blank=True)
    content = HTMLField('Artikkeli', blank=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='posts')
    image = models.ImageField(upload_to='blog_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    products = models.ManyToManyField(Product, related_name='blog_posts', blank=True)

    def __str__(self):
        return self.title

    def process_image(self):
            if self.image:
                # Open the original image
                original_img = Image.open(self.image)

                max_size = (1000, 1000)
                original_img.thumbnail(max_size)

                # Save the original image back to the field
                image_io = BytesIO()
                if self.image.name.lower().endswith('.png'):
                    # Preserve transparency for WEBP images
                    original_img.save(image_io, format='WEBP', optimize=True)
                    image_extension = 'webp'
                else:
                    # Convert to RGB for WEBP images
                    if original_img.mode == 'RGBA':
                        original_img = original_img.convert('RGB')
                    original_img.save(image_io, format='WEBP', quality=95)  # WEBP quality 95
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
                thumbnail_size = (540, int((540 / original_img.width) * original_img.height))  # Maintain aspect ratio
                thumbnail_img = original_img.resize(thumbnail_size, resample=Image.LANCZOS)  # Use Lanczos resampling for better quality

                # Save the thumbnail image
                thumbnail_io = BytesIO()
                if image_extension == 'webp':
                    # Preserve transparency for WEBP images
                    thumbnail_img.save(thumbnail_io, format='WEBP', optimize=True)
                else:
                    thumbnail_img.save(thumbnail_io, format='WEBP', quality=95)  # WEBP quality 95
                
                thumbnail_name = f"{slugify(self.title)}_{self.id}_thumbnail.{image_extension}"

                self.thumbnail = InMemoryUploadedFile(
                    thumbnail_io,
                    'ImageField',
                    thumbnail_name,
                    f'image/{image_extension}',
                    thumbnail_io.tell,
                    None
                )
    
    class Meta:
        verbose_name = 'Blogi artikkeli'
        verbose_name_plural = 'Blogi artikkelit'
    
    def save(self, *args, **kwargs):
        self.process_image()
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f"/blog/{self.category.slug}/{self.slug}/"

class AdditionalImage(models.Model):
    blog_post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='additional_images')
    image = models.ImageField(upload_to='blog_images/additional/', null=True, blank=True)

    def __str__(self):
        return f"Image for {self.blog_post.title}"

    def process_image(self):
        if self.image:
            # Open the original image
            original_img = Image.open(self.image)

            # Set the maximum size for the larger side to 800px
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

            # Create a new filename based on the blog post title and image ID
            image_name = f"{slugify(self.blog_post.title)}_{self.id}_additional.{image_extension}"

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