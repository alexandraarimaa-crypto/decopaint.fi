# google_shopping/views.py

from django.shortcuts import render
from django.http import JsonResponse
from shop.models import Category, Variant
from .api import delete_all_products, list_all_products, get_service, sync_missing_products
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
from django.conf import settings
import logging
import traceback
from functools import wraps

logger = logging.getLogger(__name__)


def staging_safe(view_func):
    """Block external Merchant mutations when integration writes are disabled."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not getattr(settings, "MERCHANT_SYNC_ENABLED", True):
            return JsonResponse({
                "status": "error",
                "message": "Merchant Center -muutokset on poistettu käytöstä tässä ympäristössä.",
            }, status=403)
        return view_func(request, *args, **kwargs)

    return wrapper

def admin_required(view_func):
    """
    Decorator to ensure user is superuser.
    """
    return user_passes_test(lambda u: u.is_superuser, login_url='/admin/login/')(view_func)

def handle_api_error(view_func):
    """
    Decorator to handle API errors and return proper JSON responses.
    """
    def wrapper(request, *args, **kwargs):
        try:
            return view_func(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"API Error in {view_func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            
            return JsonResponse({
                'status': 'error',
                'message': f'Palvelinvirhe: {str(e)}',
                'error_type': type(e).__name__
            }, status=500)
    
    return wrapper

@admin_required
@require_POST
@staging_safe
@handle_api_error
def incremental_update_single_variant_view(request):
    """
    View for optimized incremental update using only one best variant per product.
    """
    logger.info(f"Single variant incremental update requested with params: {request.GET}")
    
    from .tasks import incremental_update_optimized_single_variant
    
    # Get parameters from request
    product_batch_size = int(request.GET.get('product_batch_size', 20))
    max_workers = int(request.GET.get('max_workers', 2))
    
    result = incremental_update_optimized_single_variant(
        product_batch_size=product_batch_size,
        max_workers=max_workers
    )
    return JsonResponse(result)

@admin_required  
@require_POST
@staging_safe
@handle_api_error
def full_clean_upload_single_variant_view(request):
    """
    View for full clean upload using only one best variant per product.
    """
    logger.info(f"Single variant full clean upload requested with params: {request.GET}")
    
    from .tasks import full_clean_upload_single_variant
    
    product_batch_size = int(request.GET.get('product_batch_size', 20))
    result = full_clean_upload_single_variant(product_batch_size=product_batch_size)
    return JsonResponse(result)

@admin_required
@handle_api_error
def get_best_variant_statistics_view(request):
    """
    Get statistics about best variants and optimization benefits.
    """
    logger.info("Best variant statistics requested")
    
    from .tasks import get_best_variant_statistics
    
    stats = get_best_variant_statistics()
    
    if stats:
        return JsonResponse({
            'status': 'success',
            'statistics': stats
        })
    else:
        return JsonResponse({
            'status': 'error',
            'message': 'Optimointitilastojen haku epäonnistui'
        })

@admin_required
@require_POST
@staging_safe
@handle_api_error
def delete_all_products_view(request):
    """
    View to delete all products from Google Merchant Center.
    """
    logger.info("Delete all products requested")
    
    result = delete_all_products()
    return JsonResponse(result)

@admin_required
@require_POST
@staging_safe
@handle_api_error
def delete_product_by_merchant_id_view(request):
    """
    View to delete a product from Google Merchant Center by Merchant Center product ID.
    """
    merchant_center_id = request.GET.get('merchant_center_id') or request.POST.get('merchant_center_id')
    
    if not merchant_center_id:
        return JsonResponse({
            'status': 'error',
            'message': 'Merchant Center -tuote-ID vaaditaan.'
        }, status=400)
    
    # Clean the input - remove any whitespace and convert to uppercase
    merchant_center_id = merchant_center_id.strip().upper()
    
    logger.info(f"Delete product by Merchant Center ID requested: {merchant_center_id}")
    
    from .api import delete_product_by_merchant_center_id
    result = delete_product_by_merchant_center_id(merchant_center_id)
    
    return JsonResponse(result)

@admin_required
@handle_api_error
def merchant_center_info_view(request):
    """
    Returns connection status and total number of products in Google Merchant Center.
    """
    logger.info("Merchant Center info requested")
    
    try:
        service = get_service()
        all_products = list_all_products(service)
        total_products = len(all_products)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Yhdistetty Google Merchant Centeriin',
            'total_products': total_products
        })
    except Exception as e:
        logger.error(f"Merchant Center connection failed: {e}")
        return JsonResponse({
            'status': 'error',
            'message': f"Yhteys epäonnistui: {str(e)}"
        })

@admin_required
@require_POST
@staging_safe
@handle_api_error
def sync_missing_products_view(request):
    """
    View to synchronize products between website and Google Shopping.
    Removes products from Google Shopping that are no longer available on the website.
    """
    logger.info("Product synchronization requested")
    
    from .tasks import sync_missing_products_task
    
    # Run synchronization as async task
    from django_q.tasks import async_task
    async_task(
        'google_shopping.tasks.sync_missing_products_task',
        hook='google_shopping.tasks.sync_missing_products_complete_hook'
    )
    
    return JsonResponse({
        'status': 'success',
        'message': 'Tuotesynkronointi aloitettu taustalla. Tarkista lokit tiedon saamiseksi.'
    })

@admin_required
def google_shopping_upload_page(request):
    """
    Admin page for Google Shopping upload operations.
    """
    logger.info("Google Shopping admin page accessed")
    return render(request, 'admin/google_shopping_upload.html')
