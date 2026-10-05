from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from shop.models import Product, Variant
from django_q.tasks import async_task
from django.conf import settings
import logging
import time

logger = logging.getLogger(__name__)

# Track recently updated products to avoid duplicate signals
_recently_updated_products = {}
_recently_updated_variants = {}

@receiver(post_save, sender=Product)
def update_product_in_merchant_center(sender, instance, created, **kwargs):
    """
    When a Product is updated, update the corresponding product in Google Merchant Center.
    """
    if (
        getattr(settings, "MERCHANT_SYNC_ENABLED", True)
        and not created
        and not kwargs.get('raw', False)
    ):
        try:
            # Rate limiting: only process one signal per product per 10 seconds
            current_time = time.time()
            product_key = f"product_{instance.id}"
            
            if product_key in _recently_updated_products:
                if current_time - _recently_updated_products[product_key] < 10:
                    logger.debug(f"Skipping duplicate signal for product {instance.id}")
                    return
            
            _recently_updated_products[product_key] = current_time
            
            logger.info(f"Product {instance.id} updated. Scheduling Google Merchant Center update.")
            
            # Use the main update function directly
            async_task(
                'google_shopping.tasks.process_single_product_update', 
                instance.id
            )
            
        except Exception as e:
            logger.error(f"Error handling product {instance.id} update: {e}")

@receiver(post_save, sender=Variant)
def update_variant_in_merchant_center(sender, instance, created, **kwargs):
    """
    When a Variant is updated, check if it affects the uploaded variant for its product.
    """
    if (
        getattr(settings, "MERCHANT_SYNC_ENABLED", True)
        and instance.product_id
        and not kwargs.get('raw', False)
    ):
        try:
            # Rate limiting: only process one signal per variant per 10 seconds
            current_time = time.time()
            variant_key = f"variant_{instance.id}"
            
            if variant_key in _recently_updated_variants:
                if current_time - _recently_updated_variants[variant_key] < 10:
                    logger.debug(f"Skipping duplicate signal for variant {instance.id}")
                    return
            
            _recently_updated_variants[variant_key] = current_time
            
            logger.info(f"Variant {instance.id} updated. Scheduling update for product {instance.product_id}.")
            
            # Use the main update function directly
            async_task(
                'google_shopping.tasks.process_single_product_update', 
                instance.product_id
            )
            
        except Exception as e:
            logger.error(f"Error handling variant {instance.id} update: {e}")

@receiver(post_delete, sender=Variant)
def delete_variant_from_merchant_center(sender, instance, **kwargs):
    """
    When a Variant is deleted, check if it was the uploaded variant for its product.
    """
    if getattr(settings, "MERCHANT_SYNC_ENABLED", True) and instance.product_id:
        try:
            # Rate limiting for deletions too
            current_time = time.time()
            variant_key = f"variant_delete_{instance.id}"
            
            if variant_key in _recently_updated_variants:
                if current_time - _recently_updated_variants[variant_key] < 10:
                    logger.debug(f"Skipping duplicate delete signal for variant {instance.id}")
                    return
            
            _recently_updated_variants[variant_key] = current_time
            
            logger.info(f"Variant {instance.id} deleted. Checking product {instance.product_id}.")
            
            # Process immediately since this is a deletion
            async_task(
                'google_shopping.tasks.process_single_product_update', 
                instance.product_id
            )
            
        except Exception as e:
            logger.error(f"Error handling variant {instance.id} deletion: {e}")

def clear_recently_updated_cache():
    """
    Clear the cache of recently updated products and variants.
    This should be called periodically to prevent memory growth.
    """
    global _recently_updated_products, _recently_updated_variants
    current_time = time.time()
    
    # Remove old entries (older than 1 hour)
    _recently_updated_products = {
        k: v for k, v in _recently_updated_products.items() 
        if current_time - v < 3600
    }
    
    _recently_updated_variants = {
        k: v for k, v in _recently_updated_variants.items() 
        if current_time - v < 3600
    }
