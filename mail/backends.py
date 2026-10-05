from django.core.mail.backends.smtp import EmailBackend


class LocalSMTPEmailBackend(EmailBackend):
    """Deliver queued website mail through the cPanel host's local Exim MTA."""

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(
            host="localhost",
            port=25,
            username="",
            password="",
            use_tls=False,
            use_ssl=False,
            timeout=30,
            fail_silently=fail_silently,
        )
