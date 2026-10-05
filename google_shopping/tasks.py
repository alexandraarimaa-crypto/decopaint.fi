# google_shopping/tasks.py

from django_q.tasks import async_task
from django.conf import settings
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import time
from shop.models import Category, Variant, ProductImage
from django.db.models import Min, Q
from google_shopping.api import (
    add_product,
    delete_all_products,
    delete_product_by_offer_id,
    get_service,
    is_product_managed_by_service,
    list_all_products,
    sync_missing_products,
    update_product,
)
import logging

logger = logging.getLogger(__name__)

MONEY = Decimal('0.01')


def get_storefront_variant_for_product(product_id):
    """Return the variant selected by the product page on its first load."""
    variants = Variant.objects.filter(
        product_id=product_id,
        active=True,
        product__available=True,
    ).select_related('product')
    first_variant = variants.order_by('id').first()
    if first_variant is None:
        return None

    first_size = (
        variants.exclude(size__isnull=True)
        .exclude(size='')
        .values('size')
        .annotate(min_price=Min('price'))
        .order_by('min_price', 'size')
        .first()
    )
    if first_size:
        candidates = variants.filter(size=first_size['size'])
    else:
        candidates = variants.filter(Q(size='') | Q(size__isnull=True))

    # The initial storefront request has no base, grain or gloss selected.
    for field in ('base', 'grain', 'gloss'):
        candidates = candidates.filter(Q(**{field: ''}) | Q(**{f'{field}__isnull': True}))

    product = first_variant.product
    use_color1 = bool(getattr(product, 'use_color1_palette', False))
    use_color2 = bool(getattr(product, 'use_color2_palette', False))
    palette_priority = getattr(product, 'palette_priority', 'color2')
    if use_color2 and (not use_color1 or palette_priority == 'color2'):
        color_field = 'color2'
    elif use_color1:
        color_field = 'color1'
    else:
        color_field = None

    if color_field is None:
        return (
            candidates.order_by('price', 'id').first()
            or variants.order_by('price', 'id').first()
        )

    colored = candidates.exclude(**{f'{color_field}__isnull': True}).exclude(
        **{color_field: ''}
    )
    white = colored.filter(
        **{f'{color_field}__iexact': 'Valkoinen'}
    ).order_by('price', 'id').first()
    if white:
        return white

    colored_first = colored.order_by(color_field, 'price', 'id').first()
    if colored_first:
        return colored_first

    return (
        candidates.order_by('price', 'id').first()
        or variants.order_by('price', 'id').first()
    )


def public_regular_price(variant):
    """Calculate the customer price shown in parentheses on the storefront."""
    try:
        group_settings = variant.get_group_settings(None)
        tax_multiplier = Decimal('1') + (
            Decimal(group_settings.tax.rate) / Decimal('100')
        )
        customer_multiplier = Decimal(group_settings.multiplier.multi)
        product_multiplier = Decimal(variant.product.multiplier)
        value = (
            Decimal(variant.price)
            * tax_multiplier
            * customer_multiplier
            * product_multiplier
        )
    except (AttributeError, InvalidOperation, TypeError, ValueError) as error:
        raise ValueError(
            f'Cannot calculate public Merchant price for variant {variant.id}: {error}'
        ) from error

    if not value.is_finite() or value <= 0:
        raise ValueError(
            f'Public Merchant price must be positive for variant {variant.id}.'
        )
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)

def get_best_variant_for_product(product_id):
    """
    Find the best variant for a specific product.
    Returns the cheapest active variant.
    """
    try:
        best_variant = Variant.objects.filter(
            product_id=product_id,
            active=True,
            product__available=True,
            product__category__in=Category.objects.filter(active=True)
        ).order_by('price', 'id').first()

        return best_variant
    except Exception as e:
        logger.error(f"Error finding best variant for product {product_id}: {e}")
        return None

def get_best_variants_chunked(chunk_size=1000):
    """
    Get best variants using chunked approach to avoid memory issues.
    Processes products in chunks instead of loading everything at once.
    """
    try:
        logger.info("Starting chunked best variants search...")

        # First, get all active product IDs (this should be manageable)
        active_product_ids = Variant.objects.filter(
            active=True,
            product__available=True,
            product__category__in=Category.objects.filter(active=True)
        ).values_list('product_id', flat=True).distinct()

        total_products = active_product_ids.count()
        logger.info(f"Found {total_products} active products to process")

        if total_products == 0:
            return []

        # Convert to list and process in chunks
        product_ids_list = list(active_product_ids)
        best_variants = []

        # Process products in chunks to avoid memory issues
        for i in range(0, total_products, chunk_size):
            chunk_product_ids = product_ids_list[i:i + chunk_size]

            logger.info(f"Processing product chunk {i//chunk_size + 1}/{(total_products-1)//chunk_size + 1} ({len(chunk_product_ids)} products)")

            # For each product in this chunk, find the best variant
            for product_id in chunk_product_ids:
                try:
                    best_variant = get_best_variant_for_product(product_id)
                    if best_variant:
                        best_variants.append(best_variant)
                except Exception as e:
                    logger.error(f"Error processing product {product_id}: {e}")
                    continue

            # Small delay between chunks to avoid overwhelming the database
            if i + chunk_size < total_products:
                time.sleep(0.1)

        logger.info(f"Chunked processing completed. Found {len(best_variants)} best variants")
        return best_variants

    except Exception as e:
        logger.error(f"Chunked best variants search failed: {e}")
        return get_best_variants_simple()

def get_best_variants_simple():
    """
    Simple fallback method that uses minimal memory.
    Gets product IDs first, then processes them one by one.
    """
    try:
        logger.info("Using simple best variants method...")

        # Get all active product IDs
        active_product_ids = Variant.objects.filter(
            active=True,
            product__available=True,
            product__category__in=Category.objects.filter(active=True)
        ).values_list('product_id', flat=True).distinct()

        best_variants = []
        total_processed = 0

        for product_id in active_product_ids:
            try:
                best_variant = get_best_variant_for_product(product_id)
                if best_variant:
                    best_variants.append(best_variant)

                total_processed += 1

                # Progress logging
                if total_processed % 100 == 0:
                    logger.info(f"Processed {total_processed}/{len(active_product_ids)} products")

            except Exception as e:
                logger.error(f"Error processing product {product_id}: {e}")
                continue

        logger.info(f"Simple processing completed. Found {len(best_variants)} best variants")
        return best_variants

    except Exception as e:
        logger.error(f"Simple best variants method failed: {e}")
        return []

def get_best_variants_optimized():
    """
    Optimized method that balances performance and memory usage.
    """
    try:
        # Try the chunked method first
        return get_best_variants_chunked(chunk_size=500)
    except Exception as e:
        logger.error(f"Optimized method failed, falling back to simple: {e}")
        return get_best_variants_simple()

def incremental_update_optimized_single_variant(base_url='https://decopaint.fi', product_batch_size=20, max_workers=2):
    """
    Optimized incremental update with full synchronization.
    Updates existing products, adds missing ones, and removes products not on website.
    Uses smaller batches and better error handling.
    """
    try:
        logger.info("Starting optimized incremental update with full synchronization...")

        service = get_service()

        # Step 1: Get current products from Google Merchant Center
        logger.info("Fetching current products from Google Merchant Center...")
        uploaded_products = list_all_products(service)
        products_by_offer_id = {
            product.get('offerId'): product
            for product in uploaded_products
            if product.get('offerId')
        }
        uploaded_offer_ids = set(products_by_offer_id)
        managed_offer_ids = {
            offer_id
            for offer_id, product in products_by_offer_id.items()
            if is_product_managed_by_service(product, service)
        }
        logger.info(
            "Found %s processed products; %s are owned by this Merchant API source",
            len(uploaded_offer_ids),
            len(managed_offer_ids),
        )

        # Step 2: Get active products from website
        logger.info("Finding best variants for all active products...")
        best_variants = get_best_variants_optimized()
        total_products = len(best_variants)
        logger.info(f"Found {total_products} active products on website")

        if total_products == 0:
            return {
                'status': 'error',
                'message': 'Ei aktiivisia tuotteita verkkosivustolla.',
                'total_products': 0,
                'total_batches': 0
            }

        # Step 3: Identify products to add, update, and remove
        website_offer_ids = set()
        best_variant_map = {}

        for variant in best_variants:
            if variant.item_code:
                website_offer_ids.add(variant.item_code)
                best_variant_map[variant.item_code] = variant

        # Products that exist in both - need update
        products_to_update = website_offer_ids.intersection(managed_offer_ids)
        # Products that exist only on website - need to be added
        products_to_add = website_offer_ids - uploaded_offer_ids
        # Products owned by another source must never be overwritten (or "stolen")
        # by this integration.
        products_owned_elsewhere = (
            website_offer_ids.intersection(uploaded_offer_ids) - managed_offer_ids
        )
        # Products that exist only in this source can be removed safely.
        products_to_remove = managed_offer_ids - website_offer_ids

        logger.info(
            "Synchronization plan: Update %s, Add %s, Remove %s, Skip %s owned by another source",
            len(products_to_update),
            len(products_to_add),
            len(products_to_remove),
            len(products_owned_elsewhere),
        )

        # Step 4: Remove products that are no longer on website
        removed_count = 0
        for offer_id in products_to_remove:
            try:
                success = delete_product_by_offer_id(offer_id)
                if success:
                    removed_count += 1
                    logger.info(f"Removed product {offer_id} from Google Merchant Center")
                # Rate limiting
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error removing product {offer_id}: {e}")

        # Step 5: Process website products (both updates and additions)
        all_products_to_process = list(products_to_update) + list(products_to_add)
        total_to_process = len(all_products_to_process)

        if total_to_process == 0:
            return {
                'status': 'success',
                'message': f'Synkronointi valmis. Poistettu {removed_count} tuotetta. Ei tuotteita päivitettäväksi tai lisättäväksi.',
                'removed_count': removed_count,
                'updated_count': 0,
                'added_count': 0,
                'total_processed': 0,
                'total_batches': 0
            }

        # Convert to batches using variant IDs instead of offer_ids
        all_variant_ids = []
        for offer_id in all_products_to_process:
            variant = best_variant_map.get(offer_id)
            if variant:
                all_variant_ids.append(variant.id)

        # Use smaller batches for better stability
        product_batches = [all_variant_ids[i:i + product_batch_size] for i in range(0, total_to_process, product_batch_size)]

        total_batches = len(product_batches)
        logger.info(f"Splitting {total_to_process} products into {total_batches} batches (size: {product_batch_size} products/batch)")

        # Schedule batches with longer delays for stability
        scheduled_count = 0
        for i, batch in enumerate(product_batches):
            async_task(
                'google_shopping.tasks.process_single_variant_batch',
                batch,
                base_url,
                hook='google_shopping.tasks.single_variant_batch_complete_hook',
                group=f'google_shopping_product_batch_{i // 50}'
            )

            scheduled_count += 1

            if i % 5 == 0:  # Log more frequently
                logger.info(f"Scheduled {i}/{total_batches} product batches...")

            # Longer delay between scheduling to avoid queue overload
            if i % 3 == 0:
                time.sleep(2)

        logger.info(f"All {scheduled_count} product batches scheduled successfully.")

        return {
            'status': 'success',
            'message': f'Optimoitu asynkroninen päivitys aloitettu. Päivitettäväksi/lisättäväksi {total_to_process} tuotetta, poistettu {removed_count} tuotetta. Jaettu {total_batches} erään.',
            'total_products': total_to_process,
            'total_batches': total_batches,
            'product_batch_size': product_batch_size,
            'estimated_duration_minutes': (total_batches * 30) / 60,
            'removed_count': removed_count,
            'products_to_update': len(products_to_update),
            'products_to_add': len(products_to_add),
            'products_to_remove': len(products_to_remove),
            'products_owned_elsewhere': len(products_owned_elsewhere),
        }

    except Exception as e:
        error_msg = f"Optimoitu asynkroninen päivitys epäonnistui: {e}"
        logger.error(error_msg)
        return {
            'status': 'error',
            'message': error_msg,
            'total_products': 0,
            'total_batches': 0
        }

def process_single_variant_batch(best_variant_ids, base_url='https://decopaint.fi'):
    """
    Process a batch of best variants with better error handling and logging.
    This function now handles both updates and additions.
    """
    batch_stats = {
        'added': 0,
        'updated': 0,
        'errors': 0,
        'skipped': 0,
        'processed': 0,
        'batch_size': len(best_variant_ids)
    }

    try:
        logger.info(f"Starting to process batch of {len(best_variant_ids)} best variants...")

        service = get_service()

        # Get current Google Merchant Center products for this batch
        logger.info("Fetching current Google Merchant Center products...")
        uploaded_products = list_all_products(service)
        products_by_offer_id = {
            product.get('offerId'): product
            for product in uploaded_products
            if product.get('offerId')
        }
        logger.info(
            "Found %s existing products in Google Merchant Center",
            len(products_by_offer_id),
        )

        # Process each best variant with progress tracking
        for i, variant_id in enumerate(best_variant_ids):
            try:
                # Get the variant with optimized query
                try:
                    variant = Variant.objects.select_related('product').get(id=variant_id)
                except Variant.DoesNotExist:
                    logger.warning(f"Variant {variant_id} not found, skipping")
                    batch_stats['skipped'] += 1
                    continue

                offer_id = variant.item_code
                if not offer_id:
                    logger.warning(f"Variant {variant_id} has no item_code, skipping")
                    batch_stats['skipped'] += 1
                    continue

                # Build product data for this variant
                product_data = build_product_data_from_variant(variant, base_url)

                existing_product = products_by_offer_id.get(offer_id)
                if existing_product and not is_product_managed_by_service(
                    existing_product, service
                ):
                    logger.warning(
                        "Skipping %s because it is owned by another Merchant data source",
                        offer_id,
                    )
                    batch_stats['skipped'] += 1
                    continue

                # Check if this integration owns the input and update/add accordingly.
                if existing_product:
                    logger.info(f"Updating existing product: {offer_id}")
                    update_product(product_data)
                    batch_stats['updated'] += 1
                else:
                    logger.info(f"Adding new product: {offer_id}")
                    add_product(product_data)
                    batch_stats['added'] += 1

                batch_stats['processed'] += 1

                # Progress logging
                if (i + 1) % 5 == 0:
                    logger.info(f"Processed {i + 1}/{len(best_variant_ids)} variants in current batch")

                # Rate limiting - 3 seconds between API calls for stability
                if i < len(best_variant_ids) - 1:
                    time.sleep(3)

            except Exception as e:
                logger.error(f"Error processing best variant {variant_id}: {e}")
                batch_stats['errors'] += 1

                # Longer delay on error
                time.sleep(10)

        logger.info(f"Single variant batch processed successfully: {batch_stats}")
        return batch_stats

    except Exception as e:
        logger.error(f"Single variant batch processing failed: {e}")
        return {
            'errors': len(best_variant_ids),
            'processed': 0,
            'batch_failed': True,
            'error_message': str(e)
        }

def single_variant_batch_complete_hook(task):
    """
    Hook function called when a single variant batch task completes.
    """
    try:
        if task.success:
            result = task.result
            logger.info(f"Single variant batch completed successfully: {result}")
        else:
            logger.error(f"Single variant batch failed: {task.result}")
    except Exception as e:
        logger.error(f"Error in single variant batch hook: {e}")

def full_clean_upload_single_variant(base_url='https://decopaint.fi', product_batch_size=20):
    """
    Full clean upload with better memory management.
    """
    try:
        logger.info("Starting full clean upload with single variant per product...")

        # Step 1: Delete all existing products
        logger.info("Deleting all existing products from Google Merchant Center...")
        delete_result = delete_all_products()
        if delete_result['status'] == 'error':
            return delete_result

        logger.info("All old products deleted. Starting new product upload...")

        # Step 2: Get only the best variants for each product
        logger.info("Finding best variants for all products...")
        best_variants = get_best_variants_optimized()

        total_products = len(best_variants)
        logger.info(f"Best variants found for {total_products} products")

        if total_products == 0:
            return {
                'status': 'error',
                'message': 'Ei aktiivisia tuotteita ladattavaksi.',
                'total_products': 0,
                'total_batches': 0
            }

        # Convert to list of variant IDs
        best_variant_ids = [variant.id for variant in best_variants]

        # Step 3: Process in smaller batches
        product_batches = [best_variant_ids[i:i + product_batch_size] for i in range(0, total_products, product_batch_size)]

        scheduled_count = 0
        for i, batch in enumerate(product_batches):
            async_task(
                'google_shopping.tasks.process_upload_single_variant_batch',
                batch,
                base_url,
                hook='google_shopping.tasks.upload_single_variant_batch_complete_hook',
                group='google_shopping_upload_products'
            )

            scheduled_count += 1

            if i % 5 == 0:
                logger.info(f"Scheduled upload product batch {i}/{len(product_batches)}")

            # Delay between scheduling
            if i % 3 == 0:
                time.sleep(2)

        return {
            'status': 'success',
            'message': f'Täysi lataus aloitettu. {total_products} tuotetta jaettu {len(product_batches)} erään.',
            'total_products': total_products,
            'total_batches': len(product_batches)
        }

    except Exception as e:
        error_msg = f"Täysi lataus epäonnistui: {e}"
        logger.error(error_msg)
        return {
            'status': 'error',
            'message': error_msg
        }

def process_upload_single_variant_batch(best_variant_ids, base_url='https://decopaint.fi'):
    """
    Process a batch of best variants for upload during full clean upload.
    Each variant represents one product.
    """
    batch_stats = {
        'success': 0,
        'errors': 0,
        'skipped': 0,
        'owned_elsewhere': 0,
    }

    # A full refresh must not take ownership of products maintained manually in
    # Merchant Center.  Merchant API's insert call can otherwise move a matching
    # offer ID to this source.
    service = get_service()
    products_by_offer_id = {
        product.get('offerId'): product
        for product in list_all_products(service)
        if product.get('offerId')
    }

    for variant_id in best_variant_ids:
        try:
            # Get the variant
            try:
                variant = Variant.objects.select_related('product').get(id=variant_id)
            except Variant.DoesNotExist:
                batch_stats['skipped'] += 1
                continue

            offer_id = variant.item_code
            if not offer_id:
                batch_stats['skipped'] += 1
                continue

            existing_product = products_by_offer_id.get(offer_id)
            if existing_product and not is_product_managed_by_service(
                existing_product, service
            ):
                logger.warning(
                    "Skipping %s during full refresh because it is owned by another Merchant data source",
                    offer_id,
                )
                batch_stats['skipped'] += 1
                batch_stats['owned_elsewhere'] += 1
                continue

            # Upload this variant (which represents the best variant for its product)
            product_data = build_product_data_from_variant(variant, base_url)
            add_product(product_data)
            products_by_offer_id[offer_id] = {
                'offerId': offer_id,
                'dataSource': service.data_source_name,
            }
            batch_stats['success'] += 1

            logger.debug(f"Uploaded product {variant.product_id} using best variant {variant_id}")

            # Rate limiting
            time.sleep(2)

        except Exception as e:
            logger.error(f"Error uploading best variant {variant_id}: {e}")
            batch_stats['errors'] += 1
            time.sleep(5)

    logger.info(f"Upload single variant batch completed: {batch_stats}")
    return batch_stats

def upload_single_variant_batch_complete_hook(task):
    """
    Hook function called when an upload single variant batch task completes.
    """
    try:
        if task.success:
            result = task.result
            logger.info(f"Upload single variant batch completed: {result}")
        else:
            logger.error(f"Upload single variant batch failed: {task.result}")
    except Exception as e:
        logger.error(f"Error in upload single variant hook: {e}")

def process_single_product_update(
    product_id,
    base_url='https://decopaint.fi',
    delete_if_unavailable=True,
):
    """
    Process a single product update for signals.
    Updates the product in Google Merchant Center with the current best variant.
    """
    try:
        logger.info(f"Processing single product update for product {product_id}...")

        service = get_service()

        # Get current Google Merchant Center products
        uploaded_products = list_all_products(service)
        products_by_offer_id = {
            product.get('offerId'): product
            for product in uploaded_products
            if product.get('offerId')
        }

        # Find the current best variant for this product
        best_variant = get_best_variant_for_product(product_id)

        if not best_variant:
            if not delete_if_unavailable:
                logger.info(
                    "No active variants found for order-triggered product "
                    "sync %s; skipping without deleting Merchant products.",
                    product_id,
                )
                return {
                    'status': 'skipped',
                    'reason': 'no_active_variants_delete_disabled',
                }

            logger.info(f"No active variants found for product {product_id}, checking if we need to delete from Google")
            # Check if this product exists in Google and delete it if no active variants
            # Get all variants for this product to find potential offer_ids
            product_variants = Variant.objects.filter(product_id=product_id)
            for variant in product_variants:
                existing_product = products_by_offer_id.get(variant.item_code)
                if existing_product and is_product_managed_by_service(
                    existing_product, service
                ):
                    delete_product_by_offer_id(variant.item_code)
                    logger.info(f"Deleted product {variant.item_code} from Google Merchant Center (no active variants)")
            return {'status': 'skipped', 'reason': 'no_active_variants'}

        offer_id = best_variant.item_code
        if not offer_id:
            logger.info(f"Best variant {best_variant.id} has no offer_id, skipping")
            return {'status': 'skipped', 'reason': 'no_offer_id'}

        product_data = build_product_data_from_variant(best_variant, base_url)

        existing_product = products_by_offer_id.get(offer_id)
        if existing_product and not is_product_managed_by_service(existing_product, service):
            logger.warning(
                "Skipping %s because it is owned by another Merchant data source",
                offer_id,
            )
            return {'status': 'skipped', 'reason': 'owned_by_another_data_source'}

        # Check if this integration owns the product input in Merchant Center.
        if existing_product:
            # Product exists, update it with current information
            update_product(product_data)
            logger.info(f"Updated product {offer_id} (product {product_id})")
            return {'status': 'updated', 'offer_id': offer_id}
        else:
            # Product doesn't exist, add it
            add_product(product_data)
            logger.info(f"Added new product {offer_id} (product {product_id})")
            return {'status': 'added', 'offer_id': offer_id}

    except Exception as e:
        logger.error(f"Error processing product {product_id} update: {e}")
        return {'status': 'error', 'reason': str(e)}

def process_single_product_update_delayed(product_id, base_url='https://decopaint.fi'):
    """
    Delayed version for bulk updates to avoid too many API calls.
    """
    try:
        # Additional delay for bulk operations
        time.sleep(2)
        return process_single_product_update(product_id, base_url)
    except Exception as e:
        logger.error(f"Error in delayed product {product_id} update: {e}")
        return {'status': 'error', 'reason': str(e)}


def sync_order_products(order_id, base_url='https://decopaint.fi'):
    """
    Upsert only the distinct products included in one confirmed order.

    This task intentionally disables the deletion branch used by catalog
    maintenance. An order confirmation must never remove Merchant products.
    """
    if not getattr(settings, "MERCHANT_SYNC_ENABLED", True):
        return {
            'status': 'disabled',
            'order_id': order_id,
            'product_count': 0,
        }

    from order.models import OrderItem

    product_ids = list(
        OrderItem.objects
        .filter(order_id=order_id)
        .exclude(variant__isnull=True)
        .values_list('variant__product_id', flat=True)
        .distinct()
    )

    results = []
    error_count = 0
    for product_id in product_ids:
        result = process_single_product_update(
            product_id,
            base_url,
            delete_if_unavailable=False,
        )
        results.append({
            'product_id': product_id,
            'status': result.get('status', 'unknown'),
        })
        if result.get('status') == 'error':
            error_count += 1

    return {
        'status': 'success' if error_count == 0 else 'partial',
        'order_id': order_id,
        'product_count': len(product_ids),
        'error_count': error_count,
        'results': results,
    }


def normalize_product_data_for_merchant_api(product_data):
    """
    Return a Merchant API-compatible copy of a legacy product payload.

    Legacy code used feed-style snake/mixed-case names and attached a
    store-specific field to the top-level product resource. Normalize those
    values defensively before the API client translates the payload.
    """
    normalized = dict(product_data)

    if 'pickup_method' in normalized:
        normalized.setdefault('pickupMethod', normalized.pop('pickup_method'))
    if 'pickup_SLA' in normalized:
        normalized.setdefault('pickupSla', normalized.pop('pickup_SLA'))

    # Store-specific inventory belongs in the local inventory resource, not
    # the online Merchant API product input.
    normalized.pop('storeCode', None)

    return normalized


def get_best_variant_statistics():
    """
    Get statistics about best variants for monitoring.
    """
    try:
        # Get counts without loading objects
        total_variants = Variant.objects.filter(
            active=True,
            product__available=True,
            product__category__in=Category.objects.filter(active=True)
        ).count()

        total_products = Variant.objects.filter(
            active=True,
            product__available=True,
            product__category__in=Category.objects.filter(active=True)
        ).values('product_id').distinct().count()

        # Calculate optimization ratio
        optimization_ratio = total_variants / total_products if total_products > 0 else 1
        optimization_percentage = ((total_variants - total_products) / total_variants * 100) if total_variants > 0 else 0

        # Google Merchant Center status
        try:
            service = get_service()
            uploaded_products = list_all_products(service)
            uploaded_count = len(uploaded_products)
        except Exception as e:
            logger.warning(f"Could not fetch Google Merchant Center status: {e}")
            uploaded_count = 0

        return {
            'total_products': total_products,
            'total_variants': total_variants,
            'optimization_ratio': round(optimization_ratio, 1),
            'optimization_percentage': round(optimization_percentage, 1),
            'currently_uploaded_products': uploaded_count,
            'upload_ready': total_products > 0
        }

    except Exception as e:
        logger.error(f"Best variant statistics failed: {e}")
        return None

def build_product_data_from_variant(
    variant,
    base_url='https://decopaint.fi',
    storefront_variant=None,
):
    """
    Build product data from a single variant for Google Merchant Center.
    Without color information in title and without color field.
    Includes product family from Attribute model in title.
    Includes main image from Product model and additional images from ProductImage model.
    Excludes "Kaikki tuotteet" from brand and title.
    """
    # Main image - use product image or thumbnail from Product model
    main_image_url = None

    # First try product image
    if variant.product.image and variant.product.image.url:
        main_image_url = f"{base_url}{variant.product.image.url}"
    # Then try product thumbnail
    elif variant.product.thumbnail and variant.product.thumbnail.url:
        main_image_url = f"{base_url}{variant.product.thumbnail.url}"
    # Fallback to default image
    else:
        main_image_url = f"{base_url}/static/images/default-product.jpg"

    # Additional images - get all product images from ProductImage model
    additional_image_links = []
    try:
        # Get all product images ordered by ID
        product_images = ProductImage.objects.filter(
            product=variant.product
        ).exclude(
            image__isnull=True
        ).exclude(
            image=''
        ).order_by('id')

        for product_image in product_images:
            if product_image.image and product_image.image.url:
                additional_image_url = f"{base_url}{product_image.image.url}"
                # Don't include the same image as main image
                if additional_image_url != main_image_url:
                    additional_image_links.append(additional_image_url)

        # Google allows maximum 10 additional images
        additional_image_links = additional_image_links[:10]

    except Exception as e:
        logger.warning(f"Could not get additional images for product {variant.product_id}: {e}")

    # Brand - exclude "Kaikki tuotteet"
    brand = "OIKOS"
    try:
        categories = variant.product.category.all()
        if categories:
            # Filter out "Kaikki tuotteet" from category names
            category_names = [
                category.name for category in categories
                if category.name and "kaikki tuotteet" not in category.name.lower()
            ]
            if category_names:
                brand = f"{', '.join(category_names)}, OIKOS"
    except Exception as e:
        logger.debug(f"Could not get categories for product {variant.product_id}: {e}")

    # Build product title - include family from Attribute model, exclude "Kaikki tuotteet"
    title_parts = []

    # Get family from Attribute model if exists
    try:
        # Get the first attribute with family information
        attribute = variant.product.attributes.first()
        if attribute and attribute.family:
            # Add family to title (e.g., "Efektimaali")
            title_parts.append(attribute.family)
    except Exception as e:
        logger.debug(f"Could not get family for product {variant.product_id}: {e}")

    # Add product name (remove "Kaikki tuotteet" if present)
    product_name = variant.product.name
    if "kaikki tuotteet" in product_name.lower():
        product_name = product_name.replace("Kaikki tuotteet", "").replace("kaikki tuotteet", "").strip()

    title_parts.append(product_name)

    title = ' '.join(title_parts)

    # Keep the existing stable offerId, but source price and availability from
    # the same default variant that the landing page displays.
    storefront_variant = (
        storefront_variant
        or get_storefront_variant_for_product(variant.product_id)
        or variant
    )
    price_value = format(public_regular_price(storefront_variant), 'f')

    # Availability
    availability = 'in stock'
    if getattr(storefront_variant, 'order_item', False):
        availability = 'out of stock'

    # Build product data
    product_data = {
        'offerId': variant.item_code,
        'title': title[:150],
        'description': (variant.product.description or 'Ei kuvausta')[:5000],
        'link': f'{base_url}{variant.product.get_absolute_url()}',
        'imageLink': main_image_url,
        'contentLanguage': 'fi',
        'targetCountry': 'FI',
        'channel': 'online',
        'condition': 'new',
        'availability': availability,
        'price': {'value': price_value, 'currency': 'EUR'},
        'brand': brand,
    }

    # Add additional images if any
    if additional_image_links:
        product_data['additionalImageLinks'] = additional_image_links

    # Add local pickup info only for in-stock items
    if availability == 'in stock':
        product_data.update({
            'pickupMethod': 'buy',     # Customer can pick up in store
            'pickupSla': 'same_day',   # Ready for pickup same day
        })

    # Remove empty fields
    product_data = {k: v for k, v in product_data.items() if v}

    return normalize_product_data_for_merchant_api(product_data)

def sync_missing_products_task():
    """
    Task to synchronize products between website and Google Shopping.
    Removes products from Google Shopping that are no longer available on the website.
    """
    try:
        logger.info("Starting product synchronization task...")
        result = sync_missing_products()
        logger.info(f"Product synchronization completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Product synchronization task failed: {e}")
        return {
            'status': 'error',
            'message': f'Synkronointitehtävä epäonnistui: {str(e)}'
        }

def sync_missing_products_complete_hook(task):
    """
    Hook function called when product synchronization task completes.
    """
    try:
        if task.success:
            result = task.result
            logger.info(f"Product synchronization completed: {result}")
        else:
            logger.error(f"Product synchronization failed: {task.result}")
    except Exception as e:
        logger.error(f"Error in product synchronization hook: {e}")
