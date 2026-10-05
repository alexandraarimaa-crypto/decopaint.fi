from django.contrib import admin
from .models import BlogPost, Category, AdditionalImage
from shop.models import Product

class AdditionalImageInline(admin.TabularInline):
    model = AdditionalImage
    extra = 1  # How many blank forms to display for uploading new images
    fields = ('image',)

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at')
    search_fields = ('title', 'content')
    list_filter = ('category',)
    inlines = [AdditionalImageInline]
    filter_horizontal = ('products',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
