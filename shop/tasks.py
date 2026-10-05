from django_q.tasks import async_task
import pandas as pd

def update_variant_prices(file_path, batch_size=100):
    try:
        df = pd.read_excel(file_path, dtype={"Barcode": str})
        df['Prezzo_Price'] = df['Prezzo_Price'].apply(lambda x: str(x).replace(',', '.') if pd.notna(x) else x)
        df['Prezzo_Price'] = pd.to_numeric(df['Prezzo_Price'], errors='coerce')

        for start in range(0, len(df), batch_size):
            batch = df.iloc[start:start + batch_size]
            async_task(process_batch, batch.to_dict(orient='records'))

        return "All batch tasks have been triggered."

    except Exception as e:
        return f"Error occurred: {str(e)}"

def process_batch(batch_data):
    from .models import Variant
    from django.db import transaction
    import pandas as pd
    
    price_map = {}
    barcodes = []
    for row in batch_data:
        barcode = row.get('Barcode')
        price = row.get('Prezzo_Price')
        
        if pd.isna(barcode) or pd.isna(price):
            continue
            
        try:
            # Parse barcode as integer (BigIntegerField in db)
            barcode_int = int(float(barcode))
            barcodes.append(barcode_int)
            price_map[barcode_int] = price
        except (ValueError, TypeError):
            continue
            
    if not barcodes:
        return "Processed batch, rows updated: 0"
        
    updated_rows = 0
    with transaction.atomic():
        # Fetch all matching variants in a single query
        variants = list(Variant.objects.filter(barcode__in=barcodes))
        for v in variants:
            new_price = price_map.get(v.barcode)
            if new_price is not None:
                v.price = new_price
                updated_rows += 1
                
        # Perform optimized bulk update
        if variants:
            Variant.objects.bulk_update(variants, ['price'])
            
    return f"Processed batch, rows updated: {updated_rows}"

def _send_with_immediate_retry(send_callable):
    """Retry one SMTP delivery once before Django-Q applies its longer retry."""
    for attempt in range(2):
        try:
            return send_callable()
        except Exception:
            if attempt == 1:
                raise


def send_order_confirmation_email(order_id, order_detail_url, language_code="fi"):
    from order.models import Order
    from mail.views import send_message, send_email_to_admin
    from shop.order_email import build_order_email_context

    order = Order.objects.select_related("user").get(id=order_id)
    customer_context = build_order_email_context(
        order,
        order_detail_url,
        language_code,
    )
    customer_email = (order.email or getattr(order.user, "email", "") or "").strip()

    if customer_email:
        _send_with_immediate_retry(
            lambda: send_message(
                customer_email,
                customer_context["copy"]["subject"],
                template_name="purchase_confirmation.html",
                context=customer_context,
                dedupe_key=f"order-confirmation:v2:{order.id}:customer",
                synchronous=True,
            )
        )

    # The internal copy stays Finnish, while the customer gets the language
    # selected during checkout.
    admin_context = build_order_email_context(order, order_detail_url, "fi")
    _send_with_immediate_retry(
        lambda: send_email_to_admin(
            "Uusi tilaus – Deco Paint",
            "purchase_confirmation.html",
            admin_context,
            dedupe_key=f"order-confirmation:v2:{order.id}:admin",
            synchronous=True,
        )
    )

    return f"Order confirmation emails accepted by SMTP for order {order_id}"

def send_order_status_email(order_id, status_key):
    from order.models import Order
    from mail.views import send_message
    
    # Mapping for Finnish status names
    STATUS_MAPPING = {
        'new': 'Uusi',
        'processing': 'Käsittelyssä',
        'shipped': 'Lähetetty',
        'delivered': 'Toimitettu',
        'canceled': 'Peruttu',
    }
    
    try:
        order = Order.objects.get(id=order_id)
        
        # Verify that the order status in DB actually matches the email we want to send
        if order.status != status_key:
            return f"Skipped triggering email: Order {order_id} status is '{order.status}', expected '{status_key}'"
        
        status_finnish = STATUS_MAPPING.get(status_key, status_key)
        
        subject = f"Tilaus #{order.id} on {status_finnish}"
        context = {'order': order, 'new_status': status_finnish}
        
        if order.email:
            send_message(order.email, subject,
                         template_name='order_status_change.html',
                         context=context,
                         dedupe_key=f'order-status:{order.id}:{status_key}')
                         
        return f"Order status email sent for order {order_id}"
        
    except Exception as e:
        return f"Failed to send status email for order {order_id}: {str(e)}"
