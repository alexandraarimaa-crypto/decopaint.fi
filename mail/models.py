from django.db import models


class OutboundEmailLog(models.Model):
    """Database-backed idempotency guard for automatic customer emails."""

    STATUS_SENDING = "sending"
    STATUS_SENT = "sent"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = (
        (STATUS_SENDING, "Lähetys käynnissä"),
        (STATUS_SENT, "Lähetetty"),
        (STATUS_FAILED, "Lähetys epäonnistui"),
    )

    # Store hashes rather than the recipient address or business identifier.
    dedupe_key = models.CharField(max_length=64, unique=True)
    recipient_hash = models.CharField(max_length=64)
    subject = models.CharField(max_length=255)
    template_name = models.CharField(max_length=160)
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_SENDING,
    )
    attempts = models.PositiveSmallIntegerField(default=1)
    sent_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Automaattisen sähköpostin lähetys"
        verbose_name_plural = "Automaattisten sähköpostien lähetykset"

    def __str__(self):
        return f"{self.template_name} – {self.status}"


class ReviewEmailLog(models.Model):
    """Tracks review-request emails so each order receives at most two."""

    order = models.OneToOneField(
        "order.Order",
        related_name="review_email_log",
        on_delete=models.CASCADE,
        db_constraint=False,
    )
    request_sent_at = models.DateTimeField(null=True, blank=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tuotearvostelupyynnön lähetys"
        verbose_name_plural = "Tuotearvostelupyyntöjen lähetykset"

    def __str__(self):
        return f"Tilaus #{self.order_id} – arvostelupyynnöt"
