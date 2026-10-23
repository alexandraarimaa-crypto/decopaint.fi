from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('shop', '0060_attribute_a_class_en_attribute_a_class_fi_and_more')]

    operations = [
        migrations.AddField(
            model_name='variant',
            name='price_per_m2',
            field=models.DecimalField(
                'Hinta €/m²', max_digits=10, decimal_places=2, null=True, blank=True,
                validators=[MinValueValidator(Decimal('0'))],
                help_text='Syötä käsin, esim. 4,85. Ei automaattista laskentaa.',
            ),
        ),
        migrations.AddField(
            model_name='variant',
            name='coverage_m2',
            field=models.CharField(
                'Riittoisuus (m²)', max_length=100, null=True, blank=True,
                help_text='Syötä käsin luku tai vaihteluväli, esim. 85–135. Ilman m²-yksikköä.',
            ),
        ),
    ]
