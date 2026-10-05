from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from shop.models import Category as ShopCategory, Product
from blog.models import Category as BlogCategory, BlogPost

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = "monthly"

    def items(self):
        return [
            'shop:main',
            'shop:terms',
            'shop:return',
            'shop:contact',
            'blog:blog_list',
            'b2b:start',
        ]

    def location(self, item):
        return reverse(item)


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return ShopCategory.objects.filter(active=True)

    def lastmod(self, obj):
        return obj.updated if hasattr(obj, 'updated') else None

    def location(self, obj):
        return reverse('shop:product_list_by_category', args=[obj.slug])


class VirtualCategorySitemap(Sitemap):
    """Code-only P0 categories that do not mutate the product database."""

    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return ["ulkomaalit"]

    def location(self, slug):
        return reverse("shop:product_list_by_category", args=[slug])


class ProductSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Product.objects.filter(available=True)

    def lastmod(self, obj):
        return obj.updated

    def location(self, obj):
        return reverse('shop:product_detail', args=[obj.slug])


class BlogCategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return BlogCategory.objects.all()

    def location(self, obj):
        return reverse('blog:blog_list') + f"{obj.slug}/"  # Категории блогов как /blog/category_slug/


class BlogPostSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return BlogPost.objects.all().order_by('-created_at')  # Сортировка по дате публикации

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return reverse('blog:blog_detail', args=[obj.category.slug, obj.slug])
