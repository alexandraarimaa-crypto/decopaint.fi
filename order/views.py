from django.shortcuts import render
from .models import OrderItem, Order, Variant
from shop.models import Coupon
from users.models import CustomUser
from mail.views import send_email_to_admin
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from mail.views import send_message
from django.urls import reverse
from django.shortcuts import get_object_or_404

def debug_log(message, data=None):
    """Helper function for debug logging"""
    print(f"[DEBUG] {message}")
    if data is not None:
        print(f"[DEBUG DATA] {data}")
