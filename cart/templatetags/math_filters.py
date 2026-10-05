from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def divide(value, arg):
    """Divide the value by the argument"""
    try:
        value_decimal = Decimal(str(value))
        arg_decimal = Decimal(str(arg))
        if arg_decimal == 0:
            return 0
        result = value_decimal / arg_decimal
        return result.quantize(Decimal('0.01'))
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        value_decimal = Decimal(str(value))
        arg_decimal = Decimal(str(arg))
        result = value_decimal * arg_decimal
        return result.quantize(Decimal('0.01'))
    except (ValueError, TypeError):
        return 0

@register.filter
def floatformat_decimal(value, decimal_places=2):
    """Format decimal with specified number of decimal places"""
    try:
        value_decimal = Decimal(str(value))
        return format(value_decimal, f'.{decimal_places}f')
    except (ValueError, TypeError):
        return value