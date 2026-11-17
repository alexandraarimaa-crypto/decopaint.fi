from django import template

register = template.Library()


@register.filter
def qualify_stock_delivery(value):
    # Rich-text content may encode the dash as &#8211; or &ndash;.
    # Replace the Finnish phrase without decoding any HTML entities.
    return str(value or "").replace("Nopea toimitus", "Varastotuotteiden toimitus")
