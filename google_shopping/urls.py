from django.urls import path
from . import views

urlpatterns = [
    # Optimized single variant operations
    path('incremental-update-single-variant/', views.incremental_update_single_variant_view, name='incremental_update_single_variant'),
    path('full-clean-upload-single-variant/', views.full_clean_upload_single_variant_view, name='full_clean_upload_single_variant'),
    path('best-variant-statistics/', views.get_best_variant_statistics_view, name='get_best_variant_statistics'),
    
    # Management operations
    path('delete-all/', views.delete_all_products_view, name='delete_all_products'),
    path('delete-product-by-merchant-id/', views.delete_product_by_merchant_id_view, name='delete_product_by_merchant_id'),
    path('merchant-info/', views.merchant_center_info_view, name='merchant_center_info'),
    
    # New synchronization endpoint
    path('sync-missing-products/', views.sync_missing_products_view, name='sync_missing_products'),
    
    # Admin page
    path('upload-page/', views.google_shopping_upload_page, name='google_shopping_upload_page'),
]