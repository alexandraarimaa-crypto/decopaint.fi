from django import template
from django.utils.translation import get_language
from shop.showroom import showroom_information

register = template.Library()


@register.simple_tag
def showroom_relocation():
    return showroom_information(get_language())
