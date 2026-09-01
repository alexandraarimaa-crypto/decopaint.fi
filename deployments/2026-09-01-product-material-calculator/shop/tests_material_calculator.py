from types import SimpleNamespace
from unittest import TestCase

from .material_calculator import (
    build_material_calculator,
    build_material_calculator_from_settings,
)


class Rows(list):
    def select_related(self, *args):
        return self


def package(amount, unit, label='', active=True, variant=None):
    return SimpleNamespace(
        amount=amount,
        unit=unit,
        active=active,
        variant=variant,
        variant_id=getattr(variant, 'id', None),
        display_label=label or f'{amount} {unit}',
    )


class MaterialCalculatorTests(TestCase):
    def test_automatic_calculator_remains_the_default(self):
        product = SimpleNamespace(material_calculator_manual_enabled=False)

        result = build_material_calculator(
            product,
            '10–12 m²/l',
            ['0,75 l', '2,5 l'],
            '2 kerrosta',
        )

        self.assertEqual(result['unit'], 'l')
        self.assertAlmostEqual(result['calculation_rate'], 0.2)

    def test_manual_coverage_uses_conservative_edge(self):
        result = build_material_calculator_from_settings(
            coverage_min='12',
            coverage_max='14',
            coverage_unit='m2_per_l',
            package_rows=[package('1', 'l'), package('2.5', 'l')],
        )

        self.assertEqual(result['raw'], '12–14 m²/l')
        self.assertAlmostEqual(result['calculation_rate'], 1 / 12)

    def test_manual_settings_must_be_complete(self):
        result = build_material_calculator_from_settings(
            coverage_min='12',
            coverage_max=None,
            coverage_unit='m2_per_l',
            package_rows=[package('1', 'l')],
        )

        self.assertIsNone(result)

    def test_manual_packages_must_match_output_unit(self):
        result = build_material_calculator_from_settings(
            coverage_min='12',
            coverage_max='14',
            coverage_unit='m2_per_l',
            package_rows=[package('5', 'kg')],
        )

        self.assertIsNone(result)

    def test_product_builder_filters_other_and_inactive_variants(self):
        selected_variant = SimpleNamespace(id=1, product_id=1295, active=True)
        other_variant = SimpleNamespace(id=2, product_id=999, active=True)
        inactive_variant = SimpleNamespace(id=3, product_id=1295, active=False)
        product = SimpleNamespace(
            id=1295,
            material_calculator_manual_enabled=True,
            material_calculator_coverage_min='12',
            material_calculator_coverage_max='14',
            material_calculator_unit='m2_per_l',
            material_calculator_packages=Rows([
                package('1', 'l', '1 l', variant=selected_variant),
                package('5', 'l', '5 l', variant=other_variant),
                package('10', 'l', '10 l', variant=inactive_variant),
            ]),
        )

        result = build_material_calculator(product, '', [])

        self.assertEqual([item['label'] for item in result['packages']], ['1 l'])

