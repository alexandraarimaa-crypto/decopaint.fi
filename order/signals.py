from django.db.models.signals import pre_save
from django.db import transaction
from django_q.tasks import async_task
from django.dispatch import receiver
from .models import Order
from mail.views import send_message

STATUS_MAPPING = {
    'new': 'Uusi',
    'processing': 'Käsittelyssä',
    'shipped': 'Lähetetty',
    'delivered': 'Toimitettu',
    'canceled': 'Peruttu',
}

@receiver(pre_save, sender=Order)
def check_order_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_order = Order.objects.get(pk=instance.pk)
            if old_order.status != instance.status and instance.status == 'shipped':
                # Use async task for sending status email - ONLY on successful commit
                # Pass the raw status key (instance.status) so the task can verify against DB
                transaction.on_commit(
                    lambda: async_task("shop.tasks.send_order_status_email", instance.id, instance.status)
                )
        except Order.DoesNotExist:
            pass