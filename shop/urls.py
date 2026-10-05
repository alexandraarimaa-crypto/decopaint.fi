from django.urls import path
from . import views
from django.shortcuts import redirect
from pk_postnord.views import get_point_by_postal, get_point_by_address, calc_ship_time
from django.contrib.sitemaps.views import sitemap
from .sitemaps import (
    BlogPostSitemap,
    CategorySitemap,
    ProductSitemap,
    StaticViewSitemap,
    VirtualCategorySitemap,
)

sitemaps = {
    'static': StaticViewSitemap,
    'categories': CategorySitemap,
    'virtual_categories': VirtualCategorySitemap,
    'products': ProductSitemap,
    'blog_posts': BlogPostSitemap,
}

app_name = 'shop'

urlpatterns = [
    path('', views.main, name='main'),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('feed/', views.google_shopping_feed, name='google_shopping_feed'),
    path('set-language/', views.set_language, name='set_language'),
    path("terms/", views.terms_view, name="terms"),
    path("return/", views.return_view, name="return"),
    path('api/get_cart_data/', views.get_cart_data, name='get_cart_data'),
    path("contact/", views.contact_view, name="contact"),
    path('catalog/', views.all_products, name='all_products'),
    path("catalog/search/", views.search_results, name="search_results"),
    path("load_catalog_menu/", views.load_catalog_menu, name="load_catalog_menu"),
    path("load_top_bar/", views.load_top_bar, name="load_top_bar"),
    path("load_shopping_bag/", views.load_shopping_bag, name="load_shopping_bag"),
    path("load_main_popular/", views.load_main_popular, name="load_main_popular"),
    path("get_postal/", get_point_by_postal, name="get_postal"),
    path("get_address/", get_point_by_address, name="get_address"),
    path("calc_ship/", calc_ship_time, name="calc_ship"),
    path("search/", views.search_results, name="search"),
    path('catalog/tag/<slug:tag_slug>/', views.product_list_by_tag, name='product_list_by_tag'),
    path('catalog/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('catalog/<slug:category_slug>/<slug:slug>/', lambda request, category_slug, slug: redirect('shop:product_detail', slug=slug)),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('catalog/<slug:slug>/get_variants', views.get_variants, name='get_variants'),
    path('catalog/<slug:slug>/get_attributes', views.get_attributes, name='get_attributes'),
    path('catalog/<slug:slug>/get_price', views.get_variant_price, name='get_variant_price'),
    path('catalog/<slug:slug>/save_review', views.save_review, name='save_review'),
    path('catalog/<slug:slug>/load_product_reviews', views.load_product_reviews, name='load_product_reviews'),
]
