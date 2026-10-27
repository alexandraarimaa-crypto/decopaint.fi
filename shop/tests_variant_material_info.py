import importlib
import json
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth.models import AnonymousUser, Permission
from django.core.exceptions import ValidationError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import RequestFactory, TestCase, TransactionTestCase, override_settings
from django.urls import include, path, reverse

from shop import translation  # noqa: F401
from shop.admin import ProductAdmin, VariantAdminForm, VariantMaterialInfoInline
from shop.material_info import legacy_material_conflicts, package_material_payload
from shop.models import PackageMaterialInfo, Product, Variant
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
            weight='1.00', customs_code=0, price_per_m2='9.99', coverage_m2='old small',
        )
        cls.large = Variant.objects.create(
            product=cls.product, item_code='test-10', size='10 L', price='135.67',
            weight='10.00', customs_code=0, price_per_m2='8.88', coverage_m2='old large',
        )
        cls.small_info = PackageMaterialInfo.objects.create(
            product=cls.product, size='1 L', price_per_m2='4.85', coverage_m2='8–12',
        )
        cls.large_info = PackageMaterialInfo.objects.create(
            product=cls.product, size='10 L', price_per_m2='3.45', coverage_m2='80–120',
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

    def inline_formset(self, data=None):
        request = RequestFactory().post('/admin/') if data else RequestFactory().get('/admin/')
        request.user = self.user
        inline = VariantMaterialInfoInline(Product, admin.site)
        formset = inline.get_formset(request, self.product)
        return inline, formset(data=data, instance=self.product, queryset=inline.get_queryset(request))

    def formset_data(self):
        _, formset = self.inline_formset()
        prefix = formset.prefix
        data = {f'{prefix}-TOTAL_FORMS': str(len(formset.forms)),
                f'{prefix}-INITIAL_FORMS': str(formset.initial_form_count()),
                f'{prefix}-MIN_NUM_FORMS': '0', f'{prefix}-MAX_NUM_FORMS': '1000'}
        for index, form in enumerate(formset.forms):
            base = f'{prefix}-{index}'
            data.update({f'{base}-product': str(self.product.pk),
                         f'{base}-price_per_m2': '', f'{base}-coverage_m2': '',
                         f'{base}-size': 'tampered size'})
            if form.instance.pk:
                data[f'{base}-id'] = str(form.instance.pk)
        return formset, data

    def test_size_changes_manual_information_without_changing_price_response(self):
        small = self.response_for(size='1 L')
        large = self.response_for(size='10 L')
        self.assertEqual((small['price_per_m2'], small['coverage_m2']), ('4.85', '8–12'))
        self.assertEqual((large['price_per_m2'], large['coverage_m2']), ('3.45', '80–120'))
        self.assertEqual(large['price'], '135.67')
        self.assertEqual(large['original_price'], '140.00')

    def test_all_colours_share_the_selected_package_and_products_are_isolated(self):
        for size in ('1 L', '10 L'):
            for color in ('A260', 'A200'):
                Variant.objects.create(product=self.product, size=size, color2=color, price='30',
                                       weight='1', customs_code=0, price_per_m2='77', coverage_m2=color)
                result = self.response_for(size=size, color=color)
                plain = self.response_for(size=size)
                self.assertEqual((result['price_per_m2'], result['coverage_m2']),
                                 (plain['price_per_m2'], plain['coverage_m2']))
        other = Product.objects.create(name='Other', slug='other', price='10')
        Variant.objects.create(product=other, size='10 L', price='10', weight='1', customs_code=0)
        self.assertIsNone(self.response_for(other, size='10 L')['price_per_m2'])
        self.assertNotIn('price_per_m2', self.response_for(size='missing'))
        self.assertEqual(PackageMaterialInfo.objects.filter(product=self.product).count(), 2)

    def test_weight_packages_and_single_package_multiple_colours(self):
        product = Product.objects.create(name='Weight', slug='weight', price='10')
        for color in ('Bianco', 'A260'):
            Variant.objects.create(product=product, size='5 kg', color1=color, price='10',
                                   weight='5', customs_code=0)
        PackageMaterialInfo.objects.create(product=product, size='5 kg', coverage_m2='40–60', price_per_m2='3.95')
        for color in ('Bianco', 'A260'):
            result = self.response_for(product, size='5 kg', color=color)
            self.assertEqual((result['price_per_m2'], result['coverage_m2']), ('3.95', '40–60'))

    def test_optional_values_clear_independently_and_never_fall_back_to_legacy(self):
        self.large_info.price_per_m2 = None
        self.large_info.coverage_m2 = '100'
        self.large_info.save()
        result = self.response_for(size='10 L', quantity='10')
        self.assertIsNone(result['price_per_m2'])
        self.assertEqual(result['coverage_m2'], '100')
        self.large_info.price_per_m2 = Decimal('0.00')
        self.large_info.coverage_m2 = ''
        self.large_info.save()
        result = self.response_for(size='10 L', quantity='10')
        self.assertEqual(result['price_per_m2'], '0.00')
        self.assertEqual(result['coverage_m2'], '')
        self.large_info.delete()
        self.assertEqual(package_material_payload(self.product.pk, '10 L'),
                         {'price_per_m2': None, 'coverage_m2': None})

    def test_removing_one_colour_does_not_remove_the_package_information(self):
        Variant.objects.create(product=self.product, size='1 L', color2='A260', price='30',
                               weight='1', customs_code=0)
        self.small.delete()
        result = self.response_for(size='1 L', color='A260')
        self.assertEqual((result['price_per_m2'], result['coverage_m2']), ('4.85', '8–12'))

    def test_negative_price_and_duplicate_product_size_are_rejected(self):
        self.large_info.price_per_m2 = Decimal('-0.01')
        with self.assertRaises(ValidationError):
            self.large_info.full_clean()
        with self.assertRaises(ValidationError):
            PackageMaterialInfo(product=self.product, size='1 L').full_clean()

    def test_tuotteet_has_one_pair_per_size_and_no_inputs_on_colour_form(self):
        Variant.objects.create(product=self.product, size='1 L', color2='A260', price='30',
                               weight='1', customs_code=0)
        self.client.force_login(self.user)
        response = self.client.get(reverse('admin:shop_product_change', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hinta €/m²')
        self.assertContains(response, 'Riittoisuus (m²)')
        _, formset = self.inline_formset()
        self.assertEqual(len(formset.forms), 2)
        self.assertTrue(all(form.fields['size'].disabled for form in formset.forms))
        self.assertNotIn('price_per_m2', VariantAdminForm().fields)
        self.assertNotIn('coverage_m2', VariantAdminForm().fields)
        self.assertIn(VariantMaterialInfoInline, ProductAdmin.inlines)

    def test_save_and_clear_package_only_preserve_every_variant_value(self):
        columns = ('pk', 'price', 'size', 'color1', 'color2', 'price_per_m2', 'coverage_m2')
        before = list(Variant.objects.order_by('pk').values_list(*columns))
        formset, data = self.formset_data()
        for index, form in enumerate(formset.forms):
            if form.instance.size == '1 L':
                data[f'{formset.prefix}-{index}-price_per_m2'] = '3,25'
                data[f'{formset.prefix}-{index}-coverage_m2'] = '10–20'
        inline, bound = self.inline_formset(data)
        self.assertTrue(bound.is_valid(), bound.errors)
        bound.save()
        self.small_info.refresh_from_db(); self.large_info.refresh_from_db()
        self.assertEqual(self.small_info.price_per_m2, Decimal('3.25'))
        self.assertEqual(self.small_info.coverage_m2, '10–20')
        self.assertEqual(self.small_info.size, '1 L')
        self.assertIsNone(self.large_info.price_per_m2)
        self.assertFalse(self.large_info.coverage_m2)
        self.assertEqual(list(Variant.objects.order_by('pk').values_list(*columns)), before)
        self.assertFalse(inline.can_delete)

    def test_newly_imported_size_is_editable_without_any_get_database_write(self):
        Variant.objects.create(product=self.product, size='5 kg', price='30', weight='5', customs_code=0)
        Variant.objects.create(product=self.product, size='', color2='Colour only', price='5', weight='1', customs_code=0)
        before = PackageMaterialInfo.objects.count()
        formset, data = self.formset_data()
        self.assertEqual(PackageMaterialInfo.objects.count(), before)
        self.assertEqual(len(formset.forms), 3)
        for index, form in enumerate(formset.forms):
            if form.initial.get('size') == '5 kg':
                data[f'{formset.prefix}-{index}-price_per_m2'] = '2,50'
                data[f'{formset.prefix}-{index}-coverage_m2'] = '40–60'
        _, bound = self.inline_formset(data)
        self.assertTrue(bound.is_valid(), bound.errors)
        bound.save()
        saved = PackageMaterialInfo.objects.get(product=self.product, size='5 kg')
        self.assertEqual(saved.price_per_m2, Decimal('2.50'))
        self.assertFalse(PackageMaterialInfo.objects.filter(size='tampered size').exists())
        self.assertFalse(PackageMaterialInfo.objects.filter(size='').exists())

    def test_conflicting_legacy_values_are_readonly_and_do_not_choose_a_colour(self):
        Variant.objects.create(product=self.product, size='1 L', color2='A260', price='30', weight='1',
                               customs_code=0, price_per_m2='7.20', coverage_m2='25')
        conflicts = legacy_material_conflicts(self.product.pk)
        self.assertEqual(conflicts['1 L']['price_per_m2'], [Decimal('7.20'), Decimal('9.99')])
        inline, _ = self.inline_formset()
        request = RequestFactory().get('/admin/'); request.user = self.user
        self.assertIn('legacy_values', inline.get_fields(request, self.product))
        self.assertIn('7.20', str(inline.legacy_values(self.small_info)))
        self.assertEqual(self.response_for(size='1 L', color='A260')['price_per_m2'], '4.85')

    def test_product_edit_permission_controls_shared_inline(self):
        staff = CustomUser.objects.create(username='editor', email='editor@invalid.example', is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename='change_product'))
        request = RequestFactory().get('/admin/'); request.user = staff
        inline = VariantMaterialInfoInline(Product, admin.site)
        self.assertTrue(inline.has_change_permission(request, self.product))
        self.assertTrue(inline.has_add_permission(request, self.product))
        request.user = AnonymousUser()
        self.assertFalse(inline.has_change_permission(request, self.product))
        self.assertFalse(inline.has_add_permission(request, self.product))

    def test_tuotteet_renders_with_admin_interface_inline_tabs(self):
        from admin_interface.models import Theme
        from django.core.cache import cache
        Theme.objects.create(name='Tabbed material regression', active=True,
                             show_inlines_as_tabs=True, show_fieldsets_as_tabs=True)
        cache.clear()
        self.client.force_login(self.user)
        response = self.client.get(reverse('admin:shop_product_change', args=[self.product.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'tabbed-changeform-tabs')
        self.assertContains(response, 'Hinta €/m²')
        self.assertContains(response, 'Riittoisuus (m²)')
        self.assertNotContains(response, 'test-1')


class PackageMaterialMigrationTests(TransactionTestCase):
    def test_consensus_is_copied_conflicts_and_original_values_are_preserved(self):
        executor = MigrationExecutor(connection)
        executor.migrate([('shop', '0061_variant_material_info')])
        old = executor.loader.project_state([('shop', '0061_variant_material_info')]).apps
        ProductOld = old.get_model('shop', 'Product')
        VariantOld = old.get_model('shop', 'Variant')
        product = ProductOld.objects.create(name='Migration paint', slug='migration-paint', price='10')
        for size, color, price, coverage in (
            ('1 L', 'Bianco', '4.85', '8–12'), ('1 L', 'A260', '4.85', '8–12'),
            ('1 L', 'A200', None, None),
            ('10 L', 'Bianco', '3.45', '80–120'), ('10 L', 'A260', '3.95', '80–120'),
            ('5 kg', 'Bianco', None, None), ('', 'Colour only', '1.20', '5'),
        ):
            VariantOld.objects.create(product=product, size=size, color2=color, price='10',
                                      weight='1', customs_code=0, price_per_m2=price, coverage_m2=coverage)
        fields = ('pk', 'product_id', 'size', 'color2', 'price', 'price_per_m2', 'coverage_m2')
        before = list(VariantOld.objects.order_by('pk').values_list(*fields))
        try:
            executor = MigrationExecutor(connection)
            target = [('shop', '0063_copy_unambiguous_package_material_info')]
            executor.migrate(target)
            state = executor.loader.project_state(target).apps
            Package = state.get_model('shop', 'PackageMaterialInfo')
            VariantAfter = state.get_model('shop', 'Variant')
            self.assertEqual(list(VariantAfter.objects.order_by('pk').values_list(*fields)), before)
            self.assertEqual(Package.objects.count(), 3)
            small = Package.objects.get(product_id=product.pk, size='1 L')
            self.assertEqual((small.price_per_m2, small.coverage_m2), (Decimal('4.85'), '8–12'))
            large = Package.objects.get(product_id=product.pk, size='10 L')
            self.assertIsNone(large.price_per_m2)
            self.assertEqual(large.coverage_m2, '80–120')
            self.assertIsNone(Package.objects.get(size='5 kg').coverage_m2)
            small.price_per_m2 = Decimal('2.22'); small.save()
            module = importlib.import_module('shop.migrations.0063_copy_unambiguous_package_material_info')
            module.copy_unambiguous_values(state, SimpleNamespace(connection=connection))
            small.refresh_from_db()
            self.assertEqual(small.price_per_m2, Decimal('2.22'))
        finally:
            MigrationExecutor(connection).migrate([('shop', '0063_copy_unambiguous_package_material_info')])
