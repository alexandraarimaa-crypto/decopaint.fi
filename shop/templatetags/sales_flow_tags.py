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
    return str(value or "").replace("Nopea toimitus 1–3", "Varastotuotteiden toimitus 1–3").replace(
        "Nopea toimitus 1-3", "Varastotuotteiden toimitus 1-3"
    )
