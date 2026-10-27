from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('shop', '0061_variant_material_info')]

    operations = [
        migrations.CreateModel(
            name='PackageMaterialInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('size', models.CharField('Pakkauskoko', max_length=100)),
                ('price_per_m2', models.DecimalField(
                    'Hinta €/m²', max_digits=10, decimal_places=2, null=True, blank=True,
                    validators=[MinValueValidator(Decimal('0'))],
                    help_text='Syötä käsin, esim. 4,85. Sama arvo kaikille tämän pakkauskoon sävyille.',
                )),
                ('coverage_m2', models.CharField(
                    'Riittoisuus (m²)', max_length=100, null=True, blank=True,
                    help_text='Syötä käsin luku tai vaihteluväli, esim. 85–135. Ilman m²-yksikköä.',
                )),
                ('product', models.ForeignKey(
                    to='shop.product', related_name='package_material_info', db_constraint=False,
                    on_delete=django.db.models.deletion.CASCADE,
                )),
            ],
            options={
                'verbose_name': 'Pakkauskohtainen lisätieto',
                'verbose_name_plural': 'Pakkauskohtaiset lisätiedot',
                'ordering': ('size',),
            },
        ),
        migrations.AddConstraint(
            model_name='packagematerialinfo',
            constraint=models.UniqueConstraint(fields=('product', 'size'), name='shop_material_product_size_unique'),
        ),
    ]
