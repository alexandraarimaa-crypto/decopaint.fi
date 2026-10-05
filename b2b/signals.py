from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import CompanyApplication
from mail.views import send_message

STATUS_MAPPING = {
    'new': 'Uusi',
    'accepted': 'Hyväksytty',
    'canceled': 'Hylätty',
}

@receiver(pre_save, sender=CompanyApplication)
def check_application_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_order = CompanyApplication.objects.get(pk=instance.pk)
            if old_order.status != instance.status and instance.status == 'accepted':
                status_finnish = STATUS_MAPPING.get(instance.status, instance.status)
                subject = f"Hakemuksenne on {status_finnish}"
                context = {'app': instance, 'status': status_finnish}
                send_message(instance.email, subject, template_name='application_status.html', context=context)
        except CompanyApplication.DoesNotExist:
            pass