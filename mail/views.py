import hashlib
from datetime import timedelta
from email.header import Header
from email.mime.image import MIMEImage
from email.utils import formataddr, parseaddr
from html import unescape

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db import transaction
from django.db.models import F
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags

from shop.models import StoreSettings

from .models import OutboundEmailLog


def _digest(value):
    return hashlib.sha256(str(value).strip().lower().encode("utf-8")).hexdigest()


def _claim_delivery(dedupe_key, recipient, subject, template_name):
    """Atomically reserve a logical email event or skip an existing delivery."""
    if not dedupe_key:
        return None, True

    key_hash = _digest(dedupe_key)
    recipient_hash = _digest(recipient)
    stale_before = timezone.now() - timedelta(minutes=15)

    with transaction.atomic():
        log, created = OutboundEmailLog.objects.select_for_update().get_or_create(
            dedupe_key=key_hash,
            defaults={
                "recipient_hash": recipient_hash,
                "subject": subject[:255],
                "template_name": template_name[:160],
                "status": OutboundEmailLog.STATUS_SENDING,
            },
        )

        if created:
            return log, True
        if log.sent_at or log.status == OutboundEmailLog.STATUS_SENT:
            return log, False
        if (
            log.status == OutboundEmailLog.STATUS_SENDING
            and log.updated_at >= stale_before
        ):
            return log, False

        OutboundEmailLog.objects.filter(pk=log.pk).update(
            recipient_hash=recipient_hash,
            subject=subject[:255],
            template_name=template_name[:160],
            status=OutboundEmailLog.STATUS_SENDING,
            attempts=F("attempts") + 1,
            last_error="",
            updated_at=timezone.now(),
        )
        log.refresh_from_db()
        return log, True


def _attach_brand_logo(email):
    """Keep the inline logo for clients that prefer CID images."""
    logo_path = finders.find("assets/images/email/deco-paint-logo.jpg")
    if not logo_path:
        return

    with open(logo_path, "rb") as logo_file:
        logo = MIMEImage(logo_file.read(), _subtype="jpeg")
    logo.add_header("Content-ID", "<deco-paint-logo>")
    logo.add_header("Content-Disposition", "inline", filename="deco-paint-logo.jpg")
    email.mixed_subtype = "related"
    email.attach(logo)


def _smtp_connection():
    """Use the hosting server's local MTA with a bounded timeout.

    The web app and the mail server run on the same cPanel host, so local Exim
    delivery avoids a second authenticated network login whose password can
    drift independently from the application environment.
    """
    return get_connection(
        backend="django.core.mail.backends.smtp.EmailBackend",
        host="localhost",
        port=25,
        username="",
        password="",
        use_tls=False,
        use_ssl=False,
        timeout=getattr(settings, "EMAIL_TIMEOUT", None) or 30,
    )


def _from_email_header():
    """Return a stable branded From header with RFC-compliant UTF-8 encoding."""
    configured_from = getattr(settings, "DEFAULT_FROM_EMAIL", "")
    configured_name, email_address = parseaddr(configured_from)
    email_address = email_address or configured_from
    display_name = getattr(settings, "EMAIL_FROM_NAME", "") or configured_name
    if not display_name:
        return email_address
    return formataddr((str(Header(display_name, "utf-8")), email_address))


def _reply_to_header():
    email_address = getattr(settings, "DEFAULT_REPLY_TO_EMAIL", "") or ""
    return [email_address] if email_address else None


def _plain_text_from_html(html_message):
    plain_text = unescape(strip_tags(html_message or ""))
    lines = [line.strip() for line in plain_text.splitlines()]
    return "\n".join(line for line in lines if line)


def send_prepared_message(
    email,
    recipient,
    subject,
    template_name,
    dedupe_key=None,
    fail_silently=False,
):
    """Send an already prepared Django email with idempotency protection."""
    log, should_send = _claim_delivery(
        dedupe_key,
        recipient,
        subject,
        template_name,
    )
    if not should_send:
        return False

    try:
        email.send()
    except Exception as exc:
        if log:
            OutboundEmailLog.objects.filter(pk=log.pk).update(
                status=OutboundEmailLog.STATUS_FAILED,
                last_error=str(exc)[:2000],
                updated_at=timezone.now(),
            )
        if fail_silently:
            return False
        raise

    if log:
        OutboundEmailLog.objects.filter(pk=log.pk).update(
            status=OutboundEmailLog.STATUS_SENT,
            sent_at=timezone.now(),
            last_error="",
            updated_at=timezone.now(),
        )
    return True


def send_message(
    recipient,
    subject,
    template_name,
    context=None,
    dedupe_key=None,
    fail_silently=False,
    synchronous=False,
):
    """Render and send one branded HTML message.

    Normal website calls remain asynchronous. Order-confirmation tasks use
    ``synchronous=True`` so their log is marked sent only after the SMTP
    server accepts the message, not merely after another task is queued.
    """
    template_path = f"mail/{template_name}"
    html_message = render_to_string(template_path, context)
    plain_text = _plain_text_from_html(html_message)
    connection = _smtp_connection() if synchronous else None

    email = EmailMultiAlternatives(
        subject=str(subject),
        body=plain_text,
        from_email=_from_email_header(),
        to=[recipient],
        connection=connection,
        reply_to=_reply_to_header(),
    )
    email.encoding = "utf-8"
    email.attach_alternative(html_message, "text/html")
    _attach_brand_logo(email)

    return send_prepared_message(
        email=email,
        recipient=recipient,
        subject=subject,
        template_name=template_name,
        dedupe_key=dedupe_key,
        fail_silently=fail_silently,
    )


def send_email_to_admin(
    subject,
    template,
    context,
    dedupe_key=None,
    synchronous=False,
):
    store_settings = StoreSettings.objects.first()

    if store_settings and store_settings.email:
        return send_message(
            store_settings.email,
            subject,
            template_name=template,
            context=context,
            dedupe_key=dedupe_key,
            synchronous=synchronous,
        )
    return False
