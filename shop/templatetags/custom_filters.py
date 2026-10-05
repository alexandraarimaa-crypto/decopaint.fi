from django import template
from shop.models import Product
import os

register = template.Library()

@register.filter
def replace_lt(value):
    return value.replace('LT', 'L')

@register.filter
def filename(value):
    return os.path.basename(value)

@register.filter
def get_color_type(variant):
    """Return color type based on which color field is populated"""
    if variant.color1:
        return 'color1'
    elif variant.color2:
        return 'color2'
    return ''

@register.filter
def get_color_name(variant):
    """Return color name from appropriate field"""
    return variant.color1 or variant.color2 or ''
    