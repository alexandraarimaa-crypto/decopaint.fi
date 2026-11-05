"""Template-only improvements compatible with the deployed blog view counter."""

import re

from django import template
from django.db.models import Count, Q

from blog.models import BlogPost
from blog.seo import enquiry_url, language, metadata, ui_text


register = template.Library()


@register.simple_tag
def blog_ui():
    return ui_text()


@register.simple_tag
def blog_metadata(post, request):
    return metadata(post, request)


@register.simple_tag
def blog_list_canonical(request, page):
    url = request.build_absolute_uri(request.path)
    return url + (f"?page={page.number}" if page.number > 1 else "")


@register.inclusion_tag("blog/project_help.html")
def blog_project_help(post):
    return {"post": post, "enquiry_url": enquiry_url(post), "ui": ui_text()}


@register.inclusion_tag("blog/related_guides.html")
def related_blog_guides(post):
    product_ids = post.products.values_list("pk", flat=True)
    guides = (
        BlogPost.objects.exclude(pk=post.pk)
        .select_related("category")
        .annotate(shared_products=Count("products", filter=Q(products__in=product_ids), distinct=True))
        .filter(Q(shared_products__gt=0) | Q(category_id=post.category_id))
        .order_by("-shared_products", "-created_at", "-pk")[:3]
    )
    return {"guides": guides, "ui": ui_text()}


@register.inclusion_tag("blog/product_guides.html")
def product_blog_guides(product):
    return {"guides": product.blog_posts.select_related("category").order_by("-created_at", "-pk")[:3], "ui": ui_text()}


@register.simple_tag
def blog_enquiry_context(request):
    slug = request.GET.get("guide", "")
    if not re.fullmatch(r"[-a-zA-Z0-9_]{1,200}", slug):
        return {}
    post = BlogPost.objects.filter(slug=slug).select_related("category").first()
    if post is None:
        return {}
    prompts = {
        "fi": "Artikkeli: {title}\n\nPinta-ala (m²):\nNykyinen alusta ja sen kunto:\nTila ja käyttötarkoitus:\nToivottu pinta ja sävy:\n\nTarvitsen apua materiaalien ja pakkauskokojen valintaan.",
        "sv": "Artikel: {title}\n\nYta (m²):\nNuvarande underlag och skick:\nRum och användning:\nÖnskad yta och kulör:\n\nJag behöver hjälp att välja material och förpackningsstorlekar.",
        "en": "Article: {title}\n\nArea (m²):\nExisting substrate and condition:\nRoom and intended use:\nDesired finish and colour:\n\nPlease help me choose materials and pack sizes.",
    }
    return {"post": post, "message": prompts.get(language(), prompts["fi"]).format(title=post.title)}
