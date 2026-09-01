from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.cache import cache_page
from django.shortcuts import render, redirect
from .models import Category, Product, Variant, Tag, Attribute, Review, RecentProductView, Slider, ProductImage
from .models import StoreSettings
from django.utils.translation import gettext as _
from order.models import Order
from django.db.models import Count
from cart.cart import Cart
from django.http import JsonResponse, HttpResponse, Http404
from django.template.loader import render_to_string
from django.db.models import Q
from django.views.decorators.cache import cache_page
from django.core.exceptions import ObjectDoesNotExist
from mail.views import send_email_to_admin
from django.db.models import Avg
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from datetime import timedelta
from django.utils import timezone
from .forms import ReviewForm
from django.conf import settings
from django.utils.translation import activate
from django.utils.http import url_has_allowed_host_and_scheme
from itertools import chain
from django.template import loader
from collections import defaultdict
from pathlib import Path
import gzip
import colorsys
from django.core.cache import cache
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from .analytics import build_product_event, build_search_event
from .search_engine import load_search_index, rank_products
from .seo import (
    CATALOG_SEO,
    HOME_SEO,
    TAG_CATEGORY_REDIRECTS,
    VIRTUAL_CATEGORY_TAGS,
    build_canonical,
    category_seo,
    product_seo,
)
from .product_schema import (
    absolute_product_image,
    build_product_data,
    json_for_script,
)
from .material_calculator import build_material_calculator
from types import SimpleNamespace


def _variant_query(product, selection):
    """Use the storefront's exact option-matching rules for one variant."""

    color = selection.get('color', '')
    if color == 'None':
        color = ''

    query = Q(product=product, active=True)
    if color:
        query &= Q(color1=color) | Q(color2=color)
    else:
        query &= (Q(color1='') | Q(color1__isnull=True)) & (Q(color2='') | Q(color2__isnull=True))

    for field in ('size', 'grain', 'gloss', 'base'):
        value = selection.get(field, '')
        if value:
            query &= Q(**{field: value})
        else:
            query &= Q(**{field: ''}) | Q(**{f'{field}__isnull': True})
    return query


def _resolve_variant(product, selection):
    return Variant.objects.filter(_variant_query(product, selection)).first()


def google_shopping_feed(request):
    # Fetch active categories
    active_categories = Category.objects.filter(active=True)
    
    # Fetch active variants from active categories, excluding main products
    variants = Variant.objects.filter(active=True, product__category__in=active_categories).select_related('product')
    
    # Add absolute URLs for product and variant images
    for variant in variants:
        # Main product image URL
        if variant.product.image:
            variant.product.image_url = request.build_absolute_uri(variant.product.thumbnail.url)
        else:
            variant.product.image_url = 'https://www.decopaint.fi/default_image.jpg'
        
        # Additional images from ProductImage model
        variant.product.additional_images = ProductImage.objects.filter(product=variant.product)
        for image in variant.product.additional_images:
            image.image_url = request.build_absolute_uri(image.image.url)
    
    # Load template
    template = loader.get_template('shop/base/feed.xml')
    context = {
        'variants': variants,
    }
    xml_data = template.render(context, request)

    buffer = BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='w') as f:
        f.write(xml_data.encode('utf-8'))
    
    response = HttpResponse(buffer.getvalue(), content_type='application/x-gzip')
    response['Content-Disposition'] = 'attachment; filename="feed.xml.gz"'
    return response

def set_language(request):
    """Persist a storefront language and return the customer to the same page."""
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/'
    if not url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = '/'

    response = redirect(next_url)
    if request.method != 'POST':
        return response

    language = request.POST.get('language', '')
    available_languages = {code for code, _name in settings.LANGUAGES}
    if language not in available_languages:
        return response

    activate(language)
    request.session[settings.LANGUAGE_COOKIE_NAME] = language
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        language,
        max_age=60 * 60 * 24 * 365,
        path=settings.LANGUAGE_COOKIE_PATH,
        domain=settings.LANGUAGE_COOKIE_DOMAIN,
        secure=True,
        httponly=False,
        samesite='Lax',
    )
    return response

def terms_view(request):
    store_settings = StoreSettings.objects.first()
    return render(request, 'shop/else/terms.html', {'terms': store_settings.terms})

def return_view(request):
    return render(request, 'shop/else/return.html', {})

#@cache_page(1 * 60 * 60)
def load_top_bar(request):
    store_settings = StoreSettings.objects.first()
    top_bar = store_settings.top_bar
    html_response = render_to_string('shop/base/top_bar.html', {
        'top_bar': top_bar,
    })
    return JsonResponse({'html': html_response})

def load_catalog_menu(request):
    # Fetch categories (no need for prefetch_related here)
    categories = Category.objects.filter(active=True).order_by('id')

    # Process data (same as before)
    tags = Tag.objects.all()
    purposes = Attribute.objects.exclude(purpose="").values_list('purpose', flat=True).distinct()
    applications = Attribute.objects.exclude(application="").values_list('application', flat=True).distinct()

    application_set = set(chain.from_iterable([app.split(', ') for app in applications]))
    unique_applications = sorted(application_set)

    user = None
    products = []
    if request.user.is_authenticated:
        user = request.user
        recent_views = get_last_unique_product_views(user)
        products = [view.product for view in recent_views]
    else:
        products = get_last_unique_product_views_from_session(request)

    # Prepare HTML responses for both templates
    html_response_desktop = render_to_string('shop/base/catalog_menu.html', {
        'user': user,
        'products': products,
        'categories': categories,
        'tags': tags,
        'purposes': purposes,
        'applications': unique_applications,
    })
    
    html_response_mobile = render_to_string('shop/base/mobile_catalog_menu.html', {
        'user': user,
        'products': products,
        'categories': categories,
        'tags': tags,
        'purposes': purposes,
        'applications': unique_applications,
    })

    # Return both HTML responses in the JSON response
    return JsonResponse({
        'html_desktop': html_response_desktop,
        'html_mobile': html_response_mobile
    })

def load_shopping_bag(request):
    cart = Cart(request)
    html_response = render_to_string('shop/base/shopping_bag.html', {
        'cart': cart,
    })
    return JsonResponse({'html': html_response})

def get_last_unique_product_views_from_session(request):
    # Get recent views from session
    recent_views = request.session.get('recent_views', [])

    # Create a set to store unique product IDs
    unique_product_ids = set()

    # Create a list to store the unique views
    unique_views = []

    # Iterate through recent views in reverse order
    for product_id in reversed(recent_views):
        # Check if the product ID is not in the set of unique product IDs
        if product_id not in unique_product_ids:
            # Add the product ID to the set
            unique_product_ids.add(product_id)
            # Append the product ID to the list of unique views
            unique_views.append(Product.objects.get(id=product_id))
            # Break the loop if we have collected 3 unique views
            if len(unique_views) == 4:
                break

    # Return the list of unique views
    return unique_views

def get_last_unique_product_views(user):
    # Get the recent views of the user
    recent_views = RecentProductView.objects.filter(user=user).order_by('-viewed_at')

    # Create a set to store unique product IDs
    unique_product_ids = set()

    # Create a list to store the unique views
    unique_views = []

    # Iterate through recent views in reverse order
    for view in recent_views:
        # Check if the product ID is not in the set of unique product IDs
        if view.product.id not in unique_product_ids:
            # Add the product ID to the set
            unique_product_ids.add(view.product.id)
            # Append the view to the list of unique views
            unique_views.append(view)
            # Break the loop if we have collected 3 unique views
            if len(unique_views) == 4:
                break

    # Return the list of unique views
    return unique_views

# Decorator to set the cache to last for a day (24 hours)
#@cache_page(24 * 60 * 60)
def contact_view(request):
    store_settings = StoreSettings.objects.first()

    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        message = request.POST.get('message')

        subject = f"Viesti Decopaint sivulta"
        template = "contact_email.html"

        context = {
            "name": name,
            "email": email,
            "phone": phone,
            "message": message,
        }
        send_email_to_admin(subject, template, context)

    # Render the contact page
    return render(request, 'shop/else/contact.html', {'open_time': store_settings.open_time})

def get_cart_data(request):
    return render(request, 'cart/cart_modal.html', {})

#@cache_page(15 * 60)
def legacy_catalog_index(request, slug):
    """Redirect an old catalogue URL to the current product or category URL."""

    if Product.objects.filter(slug=slug).exists():
        return redirect("shop:product_detail", slug=slug, permanent=True)
    if Category.objects.filter(slug=slug).exists():
        return redirect(
            "shop:product_list_by_category",
            category_slug=slug,
            permanent=True,
        )
    raise Http404


def main(request):
    # Filter before rendering so the first loop item is also the first visible
    # slide.  The template can then safely give that LCP image eager/high
    # priority loading instead of accidentally marking it as lazy.
    slider = list(
        Slider.objects.filter(active=True)
        .only('title', 'info', 'link_text', 'link', 'image', 'order')
        .order_by('order')
    )
    hero_mobile_image = ''
    if (
        slider
        and slider[0].image
        and slider[0].image.name
        == 'slider_images/oikos-corte-interna-2020_lg_tMqGfUs_I0Ar3IF_bSOItg3_vyCYWuR_ub1boFh_Wsi3p_631QBXR.webp'
    ):
        hero_mobile_image = 'assets/images/main/oikos-ottocento-lounge-mobile-780x1200.webp'
    context = {
        'slider': slider,
        'hero_mobile_image': hero_mobile_image,
        'seo': HOME_SEO,
        'canonical_url': build_canonical(request),
    }
    return render(request, 'shop/else/main.html', context)


def load_main_popular(request):
    """
    Load products from discount category (ID 90) including subcategories
    """
    try:
        discount_category = Category.objects.get(id=90)
        # Get all descendants including the category itself
        descendant_categories = discount_category.get_descendants(include_self=True)
        
        # Get products from discount category and its subcategories
        discount_products = Product.objects.filter(
            category__in=descendant_categories,
            available=True
        )[:8]
        
    except Category.DoesNotExist:
        # Fallback if discount category doesn't exist
        discount_products = Product.objects.filter(available=True)[:8]
    
    # Add dummy fields for template
    for product in discount_products:
        product.avg_rating = None
        product.rating_percent = 0
        product.total_reviews = 0
        product.total_orders = 0

    html_response = render_to_string('shop/else/main_popular.html', {
        'products': discount_products
    })

    return JsonResponse({'html': html_response})


def search_results(request):
    query = (request.GET.get('q') or '').strip()
    results = []

    if query:
        base_dir = Path(settings.BASE_DIR)
        index_path = Path(
            getattr(
                settings,
                'PRODUCT_SEARCH_INDEX_PATH',
                base_dir / 'search-data' / 'knowledge-base-draft.json',
            )
        )
        overrides_path = Path(
            getattr(
                settings,
                'PRODUCT_SEARCH_OVERRIDES_PATH',
                base_dir / 'search-data' / 'search-overrides.json',
            )
        )
        search_index = load_search_index(str(index_path), str(overrides_path))
        candidates = (
            Product.objects.filter(available=True)
            .prefetch_related('category', 'attributes')
            .distinct()
        )
        results = rank_products(candidates, query, search_index)

    # Set up pagination
    paginator = Paginator(results, 16)  # Show 16 products per page
    page_number = request.GET.get('page')
    try:
        paginated_results = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page
        paginated_results = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results
        paginated_results = paginator.page(paginator.num_pages)

    # Calculate average rating and percent for each product in the paginated results
    for product in paginated_results:
        reviews = product.reviews.all()
        product.avg_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
        if product.avg_rating is not None:
            product.rating_percent = product.avg_rating * 20
        else:
            product.rating_percent = 0
        product.total_reviews = reviews.count()

    limited_results = results[:12]

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Return rendered HTML of search_result.html for AJAX request
        return render(request, 'shop/product/search_result.html', {'query': query, 'results': limited_results, 'results_count': len(results)})

    # For non-AJAX request, continue to render 'shop/product/search.html'
    return render(request, 'shop/product/search.html', {
        'query': query,
        'results': paginated_results,
        'results_count': len(results),
        'ga4_event': build_search_event(query, len(results)),
        'seo': {
            'title': 'Tuotehaku | Deco Paint',
            'description': 'Hae Deco Paintin OIKOS-tuotteita nimellä tai käyttökohteella.',
            'h1': 'Tuotehaku',
        },
        'seo_robots': 'noindex,follow',
        'canonical_url': build_canonical(request),
    })


def all_products(request):
    products_per_page = 16

    # Загружаем все активные товары
    products = Product.objects.filter(available=True).distinct()

    paginator = Paginator(products, products_per_page)  # Разбиение на страницы
    page = request.GET.get('page')

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    # Рассчитываем общую цену для каждого товара
    for product in products:
        product.total_price = product.total_price(request.user)

    # Рассчитываем средний рейтинг и процент рейтинга
    for product in products:
        reviews = Review.objects.filter(product=product, active=True)
        product.avg_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
        product.rating_percent = product.avg_rating * 20 if product.avg_rating else 0
        product.total_reviews = reviews.count()

    context = {
        'category': None,
        'products': products,
        'total_products': paginator.count,
        'products_per_page': str(products_per_page),
        'seo': CATALOG_SEO,
        'canonical_url': build_canonical(request, keep_query=('page',)),
    }
    return render(request, 'shop/product/list.html', context)


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.filter(active=True)
    products_per_page = 16

    if category_slug:
        try:
            category = Category.objects.get(slug=category_slug, active=True)
            # Use distinct to avoid duplicate products
            products = Product.objects.filter(
                category=category,
                available=True,
                category__active=True,
            ).distinct()
        except Category.DoesNotExist:
            tag_slug = VIRTUAL_CATEGORY_TAGS.get(category_slug)
            if not tag_slug:
                raise Http404
            tag = get_object_or_404(Tag, slug=tag_slug)
            products = Product.objects.filter(tags=tag, available=True).distinct()
            category = SimpleNamespace(
                name='Julkisivumaalit ja ulkopinnoitteet',
                slug=category_slug,
                bg_image=tag.image,
                title='',
                info='',
                invert_colors=False,
            )
    else:
        # Use distinct to avoid duplicate products across categories
        products = Product.objects.filter(available=True, category__active=True).distinct()

    paginator = Paginator(products, products_per_page)  # items per page
    page = request.GET.get('page')

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    # Calculate total price for each product in the list
    for product in products:
        product.total_price = product.total_price(request.user)

    # Calculate average rating and percent for each product
    for product in products:
        reviews = Review.objects.filter(product=product, active=True)
        product.avg_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
        if product.avg_rating is not None:
            product.rating_percent = product.avg_rating * 20
        else:
            product.rating_percent = 0
        product.total_reviews = reviews.count()

    context = {
        'category': category,
        'products': products,
        'total_products': paginator.count,
        'products_per_page': str(products_per_page),
        'seo': category_seo(category_slug, category.name) if category else CATALOG_SEO,
        'canonical_url': build_canonical(request, keep_query=('page',)),
    }
    return render(request, 'shop/product/list.html', context)


def product_list_by_tag(request, tag_slug):
    category_slug = TAG_CATEGORY_REDIRECTS.get(tag_slug)
    if category_slug:
        return redirect(
            'shop:product_list_by_category',
            category_slug=category_slug,
            permanent=True,
        )

    try:
        tag = Tag.objects.get(slug=tag_slug)
        # Ensure distinct products when querying by tag
        products = Product.objects.filter(tags=tag, available=True).distinct()
    except Tag.DoesNotExist:
        products = []
        tag = None
    
    paginator = Paginator(products, 16)
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    # Calculate average rating and percent for each product
    for product in products:
        reviews = Review.objects.filter(product=product, active=True)
        product.avg_rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
        if product.avg_rating is not None:
            product.rating_percent = product.avg_rating * 20
        else:
            product.rating_percent = 0
        product.total_reviews = reviews.count()

    context = {
        'tag': tag,
        'products': products,
        'total_products': paginator.count,
        'seo': category_seo(tag_slug, tag.name if tag else ''),
        'seo_robots': 'noindex,follow',
        'canonical_url': build_canonical(request, keep_query=('page',)),
    }
    return render(request, 'shop/product/list_by_tag.html', context)

def product_detail(request, slug):
    product = Product.objects.filter(slug=slug, available=True).distinct().first()

    if not product:
        return render(request, 'shop/base/404.html', status=404)
    
    images_count = product.productimage_set.count()+1
    
    reviews = Review.objects.filter(product=product, active=True)
    average_rating = 0
    average_rating_value = 0
    if reviews.exists():
        average_rating = reviews.first().calculate_average_rating()
        average_rating_value = reviews.first().average_rating_value()

    user = request.user
    
    # Save users product view
    save_product_view(request, product)

    if user.is_authenticated:
        orders_with_product = Order.objects.filter(
            user=user,
            items__variant__product=product
        ).exclude(
            reviews__product=product
        ).distinct()
    else:
        orders_with_product = []

    total_reviews = reviews.count()
    review_stats = [
        {'rating': rating, 'count': reviews.filter(rating=rating).count(), 'percent': 0}
        for rating in range(5, 0, -1)
    ]

    if total_reviews != 0:
        for stat in review_stats:
            stat['percent'] = (stat['count'] / total_reviews) * 100

    # Получаем параметры из URL
    size_param = request.GET.get('size', '')
    color_param = request.GET.get('color', '')
    grain_param = request.GET.get('grain', '')
    gloss_param = request.GET.get('gloss', '')
    base_param = request.GET.get('base', '')

    # Получаем уникальные варианты для фильтров
    from django.db.models import Min

    # Optimize sizes - get unique sizes sorted by minimum price using DB aggregation
    sizes_data = (Variant.objects.filter(product=product, active=True)
                  .exclude(size__isnull=True).exclude(size='')
                  .values('size')
                  .annotate(min_price=Min('price'))
                  .order_by('min_price'))
    
    unique_sizes_set = []
    size_seen = set()
    for item in sizes_data:
        s_stripped = item['size'].strip()
        if s_stripped not in size_seen:
            size_seen.add(s_stripped)
            unique_sizes_set.append(s_stripped)

    # Optimize grains - DB level distinct
    grains_data = (Variant.objects.filter(product=product, active=True)
                   .exclude(grain__isnull=True).exclude(grain='')
                   .values_list('grain', flat=True)
                   .distinct())
    unique_grains_set = [g.strip() for g in grains_data if g.strip()]

    # Optimize glosses - DB level distinct
    glosses_data = (Variant.objects.filter(product=product, active=True)
                    .exclude(gloss__isnull=True).exclude(gloss='')
                    .values_list('gloss', flat=True)
                    .distinct())
    unique_glosses_set = [g.strip() for g in glosses_data if g.strip()]

    # Optimize bases - DB level distinct
    bases_data = (Variant.objects.filter(product=product, active=True)
                  .exclude(base__isnull=True).exclude(base='')
                  .exclude(base__icontains='base')
                  .values_list('base', flat=True)
                  .distinct())
    unique_bases_set = [b.strip() for b in bases_data if b.strip()]

    # Optimize colors - get unique color1 and color2 separately using DB level distinct, then union in Python
    colors1 = (Variant.objects.filter(product=product, active=True)
               .exclude(color1__isnull=True).exclude(color1='')
               .values_list('color1', flat=True)
               .distinct())
    colors2 = (Variant.objects.filter(product=product, active=True)
               .exclude(color2__isnull=True).exclude(color2='')
               .values_list('color2', flat=True)
               .distinct())
    
    unique_colors_set = sorted(list(set(colors1) | set(colors2)))

    product.total_price = product.total_price(request.user)

    family_attribute = product.attributes.first()
    family = family_attribute.family if family_attribute else ''
    display_name = f"{family} {product.name}".strip()
    canonical_url = build_canonical(request)
    material_calculator = build_material_calculator(
        product,
        family_attribute.sufficiency if family_attribute else '',
        unique_sizes_set,
        product.description,
        product.tech_info,
        product.properties,
        density=family_attribute.density if family_attribute else '',
    )

    # The HTML form preselects the first visible value for each non-colour
    # option. Resolve that exact tuple with the same rules as the price AJAX
    # endpoint. If no exact tuple exists, omit Offer rather than inventing a
    # product-level price or availability.
    option_lists = {
        'size': unique_sizes_set,
        'grain': unique_grains_set,
        'gloss': unique_glosses_set,
        'base': unique_bases_set,
    }
    selected_values = {
        'size': size_param,
        'color': '',
        'grain': grain_param,
        'gloss': gloss_param,
        'base': base_param,
    }
    for key, values in option_lists.items():
        if selected_values[key] not in values:
            selected_values[key] = values[0] if values else ''
    resolved_variant = _resolve_variant(product, selected_values)
    if resolved_variant is None:
        # Coloured products do not have an empty-colour variant, so the exact
        # query above normally returns nothing during the first page load.
        # Resolve one concrete variant with the visible non-colour selections
        # instead of asking structured data to price every colour/variant.
        schema_query = Q(product=product, active=True)
        for field in ('size', 'grain', 'gloss', 'base'):
            value = selected_values[field]
            if value:
                schema_query &= Q(**{field: value})
            else:
                schema_query &= (
                    Q(**{field: ''}) | Q(**{f'{field}__isnull': True})
                )
        resolved_variant = Variant.objects.filter(schema_query).order_by('id').first()

    if resolved_variant is None:
        # Independent option lists can occasionally preselect a combination
        # that does not exist. A single real active variant is still accurate
        # and keeps Product structured data valid without an all-variant scan.
        resolved_variant = (
            Variant.objects.filter(product=product, active=True)
            .order_by('id')
            .first()
        )

    if resolved_variant is not None:
        selected_values = {
            'size': resolved_variant.size or '',
            'color': resolved_variant.color1 or resolved_variant.color2 or '',
            'grain': resolved_variant.grain or '',
            'gloss': resolved_variant.gloss or '',
            'base': resolved_variant.base or '',
        }
    product_data = build_product_data(
        request=request,
        product=product,
        name=display_name,
        description=product.description,
        canonical_url=canonical_url,
        variant=resolved_variant,
        selection=selected_values,
    )
    product_image_url = absolute_product_image(request, product)

    context = {
        'product': product,
        'reviews': reviews,
        'orders_with_product': orders_with_product,
        'average_rating': average_rating,
        'average_rating_value': average_rating_value,
        'review_stats': review_stats,
        'total_reviews': total_reviews,
        'images_count': images_count,
        'glosses': unique_glosses_set,
        'bases': unique_bases_set,
        'sizes': unique_sizes_set,
        'grains': unique_grains_set,
        'colors': unique_colors_set,  # Добавляем объединенный список цветов
        'selected_size': size_param,
        'selected_color': color_param,
        'selected_grain': grain_param,
        'selected_gloss': gloss_param,
        'selected_base': base_param,
        'request': request,  # Добавляем request в контекст для template tag
        'ga4_event': build_product_event(product, request.user),
        'ga4_product_payload': build_product_event(
            product,
            request.user,
        )['params'],
        'seo': product_seo(product.slug, display_name, product.description),
        'canonical_url': canonical_url,
        'product_image_url': product_image_url,
        'product_structured_data_json': json_for_script(product_data),
        'material_calculator': material_calculator,
    }
    return render(request, 'shop/product/detail.html', context)

def save_product_view(request, product):
    if request.user.is_authenticated:
        user = request.user
        last_view = RecentProductView.objects.filter(user=user, product=product).order_by('-viewed_at').first()

        if last_view and timezone.now() - last_view.viewed_at < timedelta(minutes=5):
            return

        last_product_view = RecentProductView.objects.filter(user=user).order_by('-viewed_at').first()
        if last_product_view and last_product_view.product == product:
            return

        recent_views = RecentProductView.objects.filter(user=user).order_by('-viewed_at')
        if recent_views.count() >= 10:
            recent_views_to_delete = recent_views[9:]
            for view in recent_views_to_delete:
                view.delete()

        RecentProductView.objects.create(user=user, product=product)
    else:
        recent_views = request.session.get('recent_views', [])
        if product.id in recent_views:
            recent_views.remove(product.id)
        recent_views.append(product.id)
        if len(recent_views) > 10:
            recent_views = recent_views[-10:]
        request.session['recent_views'] = recent_views
        request.session.modified = True

def get_attributes(request, slug):
    if request.method == 'GET':
        selected_grain = request.GET.get('grain', '')
        selected_gloss = request.GET.get('gloss', '')

        product = get_object_or_404(Product, slug=slug)
        attributes = None

        if selected_gloss and not selected_grain:
            attributes = Attribute.objects.filter(product=product, gloss=selected_gloss)
        elif selected_grain and not selected_gloss:
            attributes = Attribute.objects.filter(product=product, grain=selected_grain)
        elif selected_gloss and selected_grain:
            attributes = Attribute.objects.filter(product=product, grain=selected_grain, gloss=selected_gloss)
        else:
            attributes = product.attributes.all()

        html_response = render_to_string('shop/product/attributes.html', { "attributes": attributes })
        return JsonResponse({'html': html_response})
    
    return JsonResponse({'error': 'Invalid request'})


def get_luminance(r, g, b):
    """Calculate luminance using BT.601 formula"""
    return 0.299 * r + 0.587 * g + 0.114 * b

def get_brightness_sort_key(variant):
    """
    Sort key for ordering variants by brightness (lightest first)
    Uses luminance calculation for accurate brightness perception
    """
    if variant.r is None or variant.g is None or variant.b is None:
        return (999,)  # Invalid colors to the end
    
    luminance = get_luminance(variant.r, variant.g, variant.b)
    return (-round(luminance, 4),)  # Negative for descending order (light to dark)

def get_hsv_key(variant):
    """
    HSV conversion for color analysis
    Currently not used for sorting but kept for reference
    """
    if variant.r is None or variant.g is None or variant.b is None:
        return (999, 0, 0)
    
    r, g, b = variant.r / 255.0, variant.g / 255.0, variant.b / 255.0
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    
    # Group by brightness (light ones first)
    brightness_group = 0 if v > 0.8 else 1 if v > 0.5 else 2 if v > 0.3 else 3
    
    return (
        brightness_group,  # Light ones first, then medium, then dark
        round(h, 4),      # Within group by hue
        round(s, 4)       # Then by saturation
    )
def get_variants(request, slug):
    """
    Get product variants with color selection handling - OPTIMIZED VERSION
    Always load all colors, but control display via template
    """
    product = get_object_or_404(Product, slug=slug)
    
    if request.method == 'GET':
        base_param = request.GET.get('base', '')
        size_param = request.GET.get('size', '')
        gloss_param = request.GET.get('gloss', '')
        grain_param = request.GET.get('grain', '')
        current_color = request.GET.get('current_color', '')  # Track current selected color
        
        # Convert "Perus" to empty string for gloss parameter
        if gloss_param == "Perus":
            gloss_param = ""
            
        # Build query more efficiently
        query = Q(product=product, active=True)
        
        # Apply filters with handling of empty values
        filter_mapping = {
            'size': size_param,
            'base': base_param, 
            'gloss': gloss_param,
            'grain': grain_param
        }
        
        for field, value in filter_mapping.items():
            if value:
                query &= Q(**{field: value})
            else:
                query &= (Q(**{field: ''}) | Q(**{field + '__isnull': True}))

        # FIRST: Check quickly if there are variants with colors
        variants_with_colors = Variant.objects.filter(query).filter(
            Q(color1__isnull=False) | Q(color2__isnull=False)
        ).exclude(
            Q(color1='') & Q(color2='')
        ).exists()

        # If no colors, return minimal response immediately
        if not variants_with_colors:
            context = {
                'color_variants': [],
                'product': product,
                'variants_with_colors': False,
                'current_color': current_color,  # Pass current color to template
            }
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                html_response = render_to_string('shop/product/variant_details.html', context)
                return JsonResponse({'html': html_response})
            
            return render(request, 'shop/product/detail.html', context)

        # OPTIMIZATION: Get only necessary fields for colors as dicts
        variants = Variant.objects.filter(query).values(
            'id', 'color1', 'color2', 'r', 'g', 'b', 'image', 'thumbnail'
        )

        from django.conf import settings
        media_url = getattr(settings, 'MEDIA_URL', '/media/')

        # Collect unique colors more efficiently
        unique_colors = {}
        color1_variants_count = 0
        color2_variants_count = 0
        
        for variant in variants:
            c1 = variant['color1']
            c2 = variant['color2']
            
            if c1 and product.use_color1_palette:
                color1_variants_count += 1
                if c1 not in unique_colors:
                    unique_colors[c1] = {
                        'id': variant['id'],
                        'type': 'color1',
                        'name': c1,
                        'color_value': c1,
                        'r': variant['r'] if variant['r'] is not None else 240,
                        'g': variant['g'] if variant['g'] is not None else 240,
                        'b': variant['b'] if variant['b'] is not None else 240,
                        'image': f"{media_url}{variant['image']}" if variant['image'] else '',
                        'thumbnail': f"{media_url}{variant['thumbnail']}" if variant['thumbnail'] else '',
                        'is_current': c1 == current_color
                    }
            
            if c2 and product.use_color2_palette:
                color2_variants_count += 1
                if c2 not in unique_colors:
                    unique_colors[c2] = {
                        'id': variant['id'],
                        'type': 'color2', 
                        'name': c2,
                        'color_value': c2,
                        'r': variant['r'] if variant['r'] is not None else 240,
                        'g': variant['g'] if variant['g'] is not None else 240,
                        'b': variant['b'] if variant['b'] is not None else 240,
                        'image': f"{media_url}{variant['image']}" if variant['image'] else '',
                        'thumbnail': f"{media_url}{variant['thumbnail']}" if variant['thumbnail'] else '',
                        'is_current': c2 == current_color
                    }

        # Sort colors by name with Valkoinen always first
        def name_sort_key(color_item):
            color_data = color_item[1]
            color_name = color_data['color_value'] or ''
            
            if color_name.lower() == "valkoinen":
                return ('', 0)
            
            return (color_name.lower(), 1)
        
        sorted_color_items = sorted(unique_colors.items(), key=name_sort_key)
        total_colors_count = len(sorted_color_items)
        
        # ALWAYS return all colors, but control display via template
        sorted_colors = [item[1] for item in sorted_color_items]
        
        # Determine the selected variant ID to load as a Model instance
        current_color_variant_id = None
        default_variant_id = None
        
        if sorted_colors:
            default_variant_id = sorted_colors[0]['id']
            if current_color:
                for variant_data in sorted_colors:
                    if variant_data['color_value'] == current_color:
                        current_color_variant_id = variant_data['id']
                        break
        
        # Fetch the single variant Model instance for the swatch
        current_color_variant = None
        if current_color_variant_id:
            current_color_variant = Variant.objects.filter(id=current_color_variant_id).first()
        elif default_variant_id:
            current_color_variant = Variant.objects.filter(id=default_variant_id).first()
            
        # Get active palette
        active_palette = None
        if color2_variants_count > 0 and not product.use_color1_palette:
            active_palette = {'value': 'color2', 'name': 'Uusi väripaletti'}
        elif color1_variants_count > 0 and not product.use_color2_palette:
            active_palette = {'value': 'color1', 'name': 'Vanha väripaletti'}
        elif color1_variants_count > 0 and color2_variants_count > 0:
            if product.palette_priority == 'color2' and product.use_color2_palette:
                active_palette = {'value': 'color2', 'name': 'Uusi väripaletti'}
            else:
                active_palette = {'value': 'color1', 'name': 'Vanha väripaletti'}
        elif color1_variants_count > 0:
            active_palette = {'value': 'color1', 'name': 'Vanha väripaletti'}
        elif color2_variants_count > 0:
            active_palette = {'value': 'color2', 'name': 'Uusi väripaletti'}

        # Create palette options
        available_palettes = []
        if color1_variants_count > 0 and product.use_color1_palette:
            available_palettes.append({'value': 'color1', 'name': 'Vanha väripaletti'})
        if color2_variants_count > 0 and product.use_color2_palette:
            available_palettes.append({'value': 'color2', 'name': 'Uusi väripaletti'})

        # Pre-serialize colors list to JSON for template performance optimization
        import json
        color_variants_json = json.dumps(sorted_colors)

        # Prepare response data
        context = {
            'color_variants': sorted_colors,  # Pass dicts instead of model instances
            'color_variants_json': color_variants_json,
            'product': product,
            'available_palettes': available_palettes,
            'active_palette': active_palette,
            'color1_unique': color1_variants_count,
            'color2_unique': color2_variants_count,
            'variants_with_colors': True,
            'total_colors_count': total_colors_count,
            'current_color': current_color,
            'current_color_variant': current_color_variant,
        }
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html_response = render_to_string('shop/product/variant_details.html', context)
            return JsonResponse({'html': html_response})
        
        return render(request, 'shop/product/detail.html', context)

    return JsonResponse({'error': 'Virheellinen pyyntö'})

def get_variant_price(request, slug):
    """
    Get variant price with enhanced handling for variants without colors
    and user group-based pricing
    """
    product = get_object_or_404(Product, slug=slug)

    if request.method == 'GET':
        color = request.GET.get('color', '')
        size = request.GET.get('size', '')
        grain = request.GET.get('grain', '')
        base = request.GET.get('base', '')
        gloss = request.GET.get('gloss', '')

        selection = {
            'color': color,
            'size': size,
            'grain': grain,
            'base': base,
            'gloss': gloss,
        }
        if color == 'None':
            color = ''
            selection['color'] = ''
        variant = _resolve_variant(product, selection)

        if variant:
            # Calculate prices
            discounted_price = variant.total_price(request.user)
            original_price = variant.get_price_without_discount(request.user)
            discount_percent = product.discount_percentage
            
            # Check if user belongs to Asiakas group
            is_asiakas_group = variant.is_asiakas_group(request.user)
            
            # For non-Asiakas groups, we need to calculate what the Asiakas price would be
            # to show as the "regular price"
            if not is_asiakas_group:
                # Get Asiakas group settings to calculate regular price
                from django.contrib.auth.models import Group
                try:
                    asiakas_group = Group.objects.get(name="Asiakas")
                    from shop.models import GroupSettings
                    asiakas_settings = GroupSettings.objects.get(group=asiakas_group)
                    
                    # Calculate regular price (Asiakas group price)
                    tax_multiplier = Decimal(1 + asiakas_settings.tax.rate / 100)
                    asiakas_multi = Decimal(asiakas_settings.multiplier.multi)
                    regular_price = variant.price * tax_multiplier * asiakas_multi * Decimal(product.multiplier)
                    regular_price = regular_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    
                    # Use Asiakas price as the "original price" for display
                    original_price = regular_price
                    
                except (Group.DoesNotExist, GroupSettings.DoesNotExist):
                    # Fallback if Asiakas group settings not found
                    pass

            return JsonResponse({
                'original_price': str(round(original_price, 2)),
                'price': str(round(discounted_price, 2)),
                'discount_percent': str(discount_percent),
                'stock': variant.order_item,
                'color': color,
                'is_asiakas_group': is_asiakas_group
            })
        else:
            # Check what variants actually exist
            all_variants = Variant.objects.filter(product=product, active=True)
            matching_variants = all_variants.filter(
                (Q(color1=color) | Q(color2=color)) if color else (Q(color1='') | Q(color1__isnull=True)) & (Q(color2='') | Q(color2__isnull=True))
            )
                
            return JsonResponse({'error': 'Varianttia ei löytynyt'})

    return JsonResponse({'error': 'Virheellinen pyyntö'})


def load_product_reviews(request, slug):
    product = get_object_or_404(Product, slug=slug)
    reviews = Review.objects.filter(product=product, active=True).order_by('-created')
    user = request.user

    if user.is_authenticated:
        orders_with_product = Order.objects.filter(
            user=user,
            items__variant__product=product
        ).exclude(
            reviews__product=product
        ).distinct()
    else:
        orders_with_product = []

    form = ReviewForm(product=product)

    # Calculate total number of reviews
    total_reviews = reviews.count()

    # Calculate review statistics for all possible ratings
    review_stats = [
        {'rating': rating, 'count': reviews.filter(rating=rating).count(), 'percent': 0}
        for rating in range(5, 0, -1)
    ]

    # Calculate percentages
    if total_reviews != 0:
        for stat in review_stats:
            stat['percent'] = (stat['count'] / total_reviews) * 100

    # Calculate overall rating
    total_rating = sum(review.rating for review in reviews) / total_reviews if total_reviews != 0 else 0

    # Calculate overall percentage rating
    overall_percentage_rating = (total_rating / 5) * 100

    # Prepare HTML response
    html_response = render_to_string('shop/product/reviews.html', {
        'product': product,
        'orders_with_product': orders_with_product,
        'user': user,
        'form': form,
        'reviews': reviews,
        'review_stats': review_stats,
        'reviews_count': total_reviews,
        'overall_rating': total_rating,
        'overall_percentage_rating': overall_percentage_rating,
    })

    return JsonResponse({'html': html_response})

@login_required
def save_review(request, slug):
    if request.method == 'POST':
        product = get_object_or_404(Product, slug=slug)
        order_id = request.POST.get('order')
        order = get_object_or_404(Order, id=order_id)
        user = request.user

        # Check if the user has already left a review for this product and order
        existing_review = Review.objects.filter(product=product, order=order, user=user).exists()
        if existing_review:
            error_message = _('Olet jo jättänyt arvostelun tälle tilaukselle tästä tuotteesta.')
            return JsonResponse({'error': error_message})

        form = ReviewForm(request.POST, request.FILES, product=product, order=order)
        if form.is_valid():
            review = form.save(commit=False)  # Do not save the form immediately to add the user
            review.user = user  # Add the user to the review
            review.save()  # Now save the review

            # Send email about new application to admin
            context = {'review': review}
            admin_subject = f"Uusi {review.rating} tähden arvostelu tuotteesta {review.product}"
            admin_template = "new_review.html"
            send_email_to_admin(admin_subject, admin_template, context)

            return JsonResponse({'success': True})
        else:
            errors = form.errors.as_json()
            return JsonResponse({'error': errors})
    else:
        return JsonResponse({'error': _('Invalid request')})
