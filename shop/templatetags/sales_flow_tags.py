from django import template

from shop.sales_flow import backorder_dispatch_date, product_calculator

register = template.Library()


@register.simple_tag
def sales_calculator(product):
    return product_calculator(product)


@register.simple_tag
def sales_dispatch_date():
    return backorder_dispatch_date()


@register.filter
def qualify_stock_delivery(value):
    # Rich-text content may encode the dash as &#8211; or &ndash;.
    # Replace the Finnish phrase without decoding any HTML entities.
    return str(value or "").replace("Nopea toimitus", "Varastotuotteiden toimitus")
