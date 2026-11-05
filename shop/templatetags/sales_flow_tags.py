from django import template

from shop.sales_flow import product_calculator

register = template.Library()


@register.simple_tag
def sales_calculator(product):
    return product_calculator(product)


@register.filter
def qualify_stock_delivery(value):
    # Rich-text content may encode the dash as &#8211; or &ndash;.
    # Replace the Finnish phrase without decoding any HTML entities.
    return str(value or "").replace("Nopea toimitus", "Varastotuotteiden toimitus")
