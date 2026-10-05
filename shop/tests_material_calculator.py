from unittest import TestCase

from .material_calculator import build_material_calculator, parse_sufficiency


class MaterialCalculatorTests(TestCase):
    def test_marmorino_uses_kg_and_two_documented_coats(self):
        result = build_material_calculator(
            "0,5-0,75kg/m2",
            ["1 kg", "5 kg", "20 kg"],
            "Levitä kaksi kerrosta Marmorino Naturale Fine -pinnoitetta.",
        )
        self.assertEqual(result["unit"], "kg")
        self.assertEqual(result["coats"], 2)
        self.assertEqual(result["calculation_rate"], 1.5)
        self.assertEqual(
            [item["amount"] for item in result["packages"]], [1, 5, 20]
        )

    def test_coverage_range_uses_the_conservative_edge(self):
        result = build_material_calculator(
            "10–12 m²/l", ["0,75 l", "2,5 l", "10 l"], "2 kerrosta"
        )
        self.assertEqual(result["unit"], "l")
        self.assertAlmostEqual(result["calculation_rate"], 0.2)

    def test_explicit_total_is_not_multiplied_twice(self):
        result = build_material_calculator(
            "1-1,5 kg/m² kahteen kertaan", ["5 kg", "20 kg"], "kaksi kerrosta"
        )
        self.assertEqual(result["coats"], 2)
        self.assertEqual(result["calculation_rate"], 1.5)

    def test_per_coat_consumption_is_multiplied(self):
        result = build_material_calculator(
            "1,2–1,4 kg/m² / kerros", ["5 kg", "20 kg"], "Levitä kaksi kerrosta"
        )
        self.assertEqual(result["calculation_rate"], 2.8)

    def test_unrelated_or_incompatible_values_are_rejected(self):
        self.assertIsNone(parse_sufficiency("90g/l"))
        self.assertIsNone(build_material_calculator("", ["1 l"], ""))
        self.assertIsNone(build_material_calculator("8-10m2/l", ["1 kg"], ""))

    def test_density_converts_litre_rate_to_kg_packages(self):
        result = build_material_calculator(
            "1,1-2,8m2/l", ["1 kg", "5 kg"], "", density="1,7kg/l"
        )
        self.assertEqual(result["source_unit"], "l")
        self.assertEqual(result["unit"], "kg")
        self.assertAlmostEqual(result["calculation_rate"], 1.7 / 1.1)

    def test_density_converts_kg_rate_to_litre_packages(self):
        result = build_material_calculator(
            "1,3m2/kg", ["1 L", "5 L"], "", density="1350kg/m3"
        )
        self.assertEqual(result["source_unit"], "kg")
        self.assertEqual(result["unit"], "l")
        self.assertAlmostEqual(result["calculation_rate"], (1 / 1.3) / 1.35)
