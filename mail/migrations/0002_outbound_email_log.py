from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mail", "0001_review_email_log"),
    ]

    operations = [
        migrations.CreateModel(
            name="OutboundEmailLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("dedupe_key", models.CharField(max_length=64, unique=True)),
                ("recipient_hash", models.CharField(max_length=64)),
                ("subject", models.CharField(max_length=255)),
                ("template_name", models.CharField(max_length=160)),
                ("status", models.CharField(choices=[("sending", "Lähetys käynnissä"), ("sent", "Lähetetty"), ("failed", "Lähetys epäonnistui")], default="sending", max_length=16)),
                ("attempts", models.PositiveSmallIntegerField(default=1)),
                ("sent_at", models.DateTimeField(blank=True, null=True)),
                ("last_error", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Automaattisen sähköpostin lähetys",
                "verbose_name_plural": "Automaattisten sähköpostien lähetykset",
            },
        ),
    ]
