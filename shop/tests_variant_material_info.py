import json
from decimal import Decimal
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase, override_settings
from django.urls import include, path, reverse

# SimpleAdminConfig deliberately skips unrelated application autodiscovery.
from shop import translation  # noqa: F401
from shop.admin import ProductAdmin, VariantMaterialInfoInline
from shop.models import Product, Variant
from shop.views import get_variant_price
from users.models import CustomUser

urlpatterns = [path('admin/', admin.site.urls), path('', include('config.test_urls'))]


@override_settings(ROOT_URLCONF=__name__)
class VariantMaterialInfoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.product = Product.objects.create(name='Test paint', slug='test-paint', price='20.00')
        cls.small = Variant.objects.create(
            product=cls.product, item_code='test-1', size='1 L', price='20.00',
            weight='1.00', customs_code=0, price_per_m2='4.85', coverage_m2='8–13',
        )
        cls.large = Variant.objects.create(
            product=cls.product, item_code='test-10', size='10 L', price='135.67',
            weight='10.00', customs_code=0, price_per_m2='1.01', coverage_m2='85–135',
        )
        cls.user = CustomUser.objects.create(
            email='admin@invalid.example', username='test-admin', is_staff=True, is_superuser=True,
        )

    def response_for(self, product=None, **selection):
        request = RequestFactory().get('/price/', selection)
        request.user = AnonymousUser()
        with patch.object(Variant, 'total_price', return_value=Decimal('135.67')), patch.object(
            Variant, 'get_price_without_discount', return_value=Decimal('140.00')
        ):
            return json.loads(get_variant_price(request, (product or self.product).slug).content)

    def test_selected_package_returns_its_own_manual_values(self):
        small = self.response_for(size='1 L')
        large = self.response_for(size='10 L')
        self.assertEqual((small['price_per_m2'], small['coverage_m2']), ('4.85', '8–13'))
        self.assertEqual((large['price_per_m2'], large['coverage_m2']), ('1.01', '85–135'))
        self.assertEqual(large['price'], '135.67')
        self.assertEqual(large['original_price'], '140.00')

    def test_color_and_product_do_not_leak_values(self):
        Variant.objects.create(
            product=self.product, size='10 L', color2='Blue', price='30', weight='1',
            customs_code=0, price_per_m2='7.20', coverage_m2='25',
        )
        other = Product.objects.create(name='Other', slug='other', price='10')
        Variant.objects.create(product=other, size='10 L', price='10', weight='1', customs_code=0)
        self.assertEqual(self.response_for(size='10 L', color='Blue')['price_per_m2'], '7.20')
        self.assertEqual(self.response_for(size='10 L')['price_per_m2'], '1.01')
        self.assertIsNone(self.response_for(other, size='10 L')['price_per_m2'])
        self.assertNotIn('price_per_m2', self.response_for(size='missing'))

    def test_optional_fields_clear_independently_and_are_not_calculated(self):
        self.large.price_per_m2 = None
        self.large.coverage_m2 = '100'
        self.large.save(update_fields=['price_per_m2', 'coverage_m2'])
        result = self.response_for(size='10 L', quantity='10')
        self.assertIsNone(result['price_per_m2'])
        self.assertEqual(result['coverage_m2'], '100')
        self.large.price_per_m2 = Decimal('0.00')
        self.large.coverage_m2 = ''
        self.large.save(update_fields=['price_per_m2', 'coverage_m2'])
        result = self.response_for(size='10 L', quantity='10')
        self.assertEqual(result['price_per_m2'], '0.00')
        self.assertEqual(result['coverage_m2'], '')

    def test_negative_manual_price_is_rejected(self):
        self.large.price_per_m2 = Decimal('-0.01')
        with self.assertRaises(ValidationError):
            self.large.full_clean(exclude=['barcode', 'item_code'])

    def test_tuotteet_exposes_both_fields_with_readonly_variant_identity(self):
        self.assertIn(VariantMaterialInfoInline, ProductAdmin.inlines)
        self.client.force_login(self.user)
        response = self.client.get(reverse('admin:shop_product_change', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hinta €/m²')
        self.assertContains(response, 'Riittoisuus (m²)')
        self.assertContains(response, 'test-1')
        self.assertContains(response, 'test-10')

    def test_inline_saves_and_clears_only_manual_fields(self):
        request = RequestFactory().post('/admin/')
        request.user = self.user
        inline = VariantMaterialInfoInline(Product, admin.site)
        formset_type = inline.get_formset(request, self.product)
        prefix = formset_type.get_default_prefix()
        data = {
            f'{prefix}-TOTAL_FORMS': '2', f'{prefix}-INITIAL_FORMS': '2',
            f'{prefix}-MIN_NUM_FORMS': '0', f'{prefix}-MAX_NUM_FORMS': '1000',
            f'{prefix}-0-id': str(self.small.pk), f'{prefix}-0-product': str(self.product.pk),
            f'{prefix}-0-price_per_m2': '3,25', f'{prefix}-0-coverage_m2': '10–20',
            f'{prefix}-1-id': str(self.large.pk), f'{prefix}-1-product': str(self.product.pk),
            f'{prefix}-1-price_per_m2': '', f'{prefix}-1-coverage_m2': '',
        }
        formset = formset_type(data=data, instance=self.product, queryset=inline.get_queryset(request))
        self.assertTrue(formset.is_valid(), formset.errors)
        formset.save()
        self.small.refresh_from_db()
        self.large.refresh_from_db()
        self.assertEqual(self.small.price_per_m2, Decimal('3.25'))
        self.assertEqual(self.small.coverage_m2, '10–20')
        self.assertIsNone(self.large.price_per_m2)
        self.assertFalse(self.large.coverage_m2)
        self.assertEqual(self.small.price, Decimal('20.00'))
        self.assertEqual(self.large.price, Decimal('135.67'))
        self.assertEqual(self.large.size, '10 L')
        self.assertEqual(self.product.variants.count(), 2)
        self.assertFalse(inline.can_delete)
        self.assertFalse(inline.has_add_permission(request, self.product))
