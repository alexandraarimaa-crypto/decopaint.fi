from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("order", "0010_alter_order_shipping_method"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReviewEmailLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("request_sent_at", models.DateTimeField(blank=True, null=True)),
                ("reminder_sent_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("order", models.OneToOneField(db_constraint=False, on_delete=django.db.models.deletion.CASCADE, related_name="review_email_log", to="order.order")),
            ],
            options={
                "verbose_name": "Tuotearvostelupyynnön lähetys",
                "verbose_name_plural": "Tuotearvostelupyyntöjen lähetykset",
            },
        ),
    ]
