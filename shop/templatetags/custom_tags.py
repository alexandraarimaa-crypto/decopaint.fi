from django import template
from shop.models import Product

register = template.Library()

@register.simple_tag
def calculate_total_price(product, user):
    return product.total_price(user)
