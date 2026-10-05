import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from shop.search_engine import (
    _merge_override,
    load_search_index,
    normalize_text,
    query_groups,
    rank_products,
)


def record(slug, name, product_type, *, purposes=(), surfaces=(), scope=(), typos=()):
    return {
        "slug": slug,
        "product": name,
        "keywords": {
            "exact_and_name_variants": [name],
            "brands": ["oikos"],
            "product_types": [product_type],
            "purposes": list(purposes),
            "surfaces": list(surfaces),
            "scope": list(scope),
            "methods": [],
            "controlled_misspellings": list(typos),
        },
        "technical_filters": {
            "purposes": list(purposes),
            "compatible_surfaces": list(surfaces),
            "scope": list(scope),
            "application_methods": [],
        },
    }


FIXTURE = [
    record(
        "ecoprotettivo-parquet",
        "Parkettilakka Ecoprotettivo Parquet",
        "parkettilakka",
        purposes=("suojaus",),
        surfaces=("puu", "lattia", "parketti"),
    ),
    record(
        "avf-plus-2k",
        "Vesipohjainen AVF PLUS 2K Lakka",
        "suojalakka",
        purposes=("suojaus",),
    ),
    record(
        "silkos-torino",
        "Siloksaanimaali Silkos Torino",
        "siloksaanimaali",
        surfaces=("seinä", "betoni", "rappaus"),
        scope=("ulkokäyttö",),
    ),
    record(
        "duaflex",
        "Siloksaanimaali Duaflex",
        "siloksaanimaali",
        surfaces=("seinä",),
        scope=("sisäkäyttö", "ulkokäyttö"),
    ),
    record(
        "decortina-new",
        "Eristysmaali Decortina New",
        "eristysmaali",
        purposes=("nikotiini-, noki- ja savutahrat",),
        surfaces=("seinä",),
        scope=("sisäkäyttö",),
    ),
    record(
        "biofissativo-alta-adesione",
        "Tartuntapohjamaali 250 BioFissativo Alta Adesione",
        "tartuntapohjamaali",
        purposes=("pohjustus", "tartunnan parantaminen"),
        surfaces=("PVC", "muovi", "alumiini", "laminaatti"),
    ),
    record(
        "aggrappante-ecologico",
        "Erikoispohjamaali Aggrappante Ecologico",
        "erikoispohjamaali",
        purposes=("pohjustus", "tartunnan parantaminen"),
        surfaces=("PVC", "muovi", "alumiini", "laminaatti"),
    ),
    record(
        "antiruggine-ecologico",
        "Ruosteenestoaine Antiruggine Ecologico",
        "ruosteenestoaine",
        purposes=("ruosteenesto",),
        surfaces=("metalli",),
    ),
    record(
        "sterylfix",
        "Homeenpoistoaine Sterylfix",
        "homeenpoistoaine",
        purposes=("homeenpoisto",),
        surfaces=("seinä",),
        scope=("sisäkäyttö", "ulkokäyttö"),
    ),
    record(
        "betoncryll-idrorepellente",
        "Väritön Impregnointiaine Betoncryll Idrorepellente",
        "impregnointiaine",
        purposes=("vedenhylkivyys",),
        surfaces=("betoni", "tiili", "kivi"),
        scope=("ulkokäyttö",),
    ),
    record(
        "marmorino-naturale",
        "Kalkkipinnoite Marmorino Naturale",
        "kalkkipinnoite",
        typos=("marmoriino",),
    ),
    record(
        "marmorino-naturale-fine",
        "Kalkkipinnoite Marmorino Naturale Fine",
        "kalkkipinnoite",
        typos=("marmoriino",),
    ),
    record(
        "protettivo-per-stucco-e-marmorino",
        "Suoja-Aine Protettivo Per Stucco E Marmorino",
        "suoja-aine",
        purposes=("suojaus",),
    ),
]


class SearchEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.index_path = Path(self.temp_dir.name) / "index.json"
        self.overrides_path = Path(self.temp_dir.name) / "overrides.json"
        self.index_path.write_text(json.dumps(FIXTURE), encoding="utf-8")
        self.overrides_path.write_text(
            json.dumps(
                {
                    "products": {
                        "protettivo-per-stucco-e-marmorino": {
                            "system_role": "companion",
                            "source": "fixture",
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        load_search_index.cache_clear()
        self.index = load_search_index(str(self.index_path), str(self.overrides_path))
        self.products = [
            SimpleNamespace(
                slug=item["slug"],
                name=item["product"],
                available=True,
            )
            for item in FIXTURE
        ]

    def tearDown(self):
        self.temp_dir.cleanup()

    def names(self, query):
        return [item.name for item in rank_products(self.products, query, self.index)]

    def test_normalization_and_controlled_expansion(self):
        self.assertEqual(normalize_text("SISÄ-seinä"), "sisa seina")
        self.assertEqual(query_groups("marmoriino"), [("marmorino",)])
        self.assertEqual(query_groups("puulattian lakka"), [("puu",), ("lattia",), ("lakka",)])

    def test_wood_floor_lacquer_excludes_unverified_generic_lacquer(self):
        self.assertEqual(
            self.names("puulattian lakka"),
            ["Parkettilakka Ecoprotettivo Parquet"],
        )

    def test_exterior_siloxane_wall_requires_all_concepts(self):
        self.assertEqual(
            self.names("siloksaanimaali ulkoseinä"),
            ["Siloksaanimaali Duaflex", "Siloksaanimaali Silkos Torino"],
        )

    def test_pvc_primer_does_not_leak_mislinked_antirust_product(self):
        self.assertEqual(
            self.names("PVC pohjamaali"),
            [
                "Erikoispohjamaali Aggrappante Ecologico",
                "Tartuntapohjamaali 250 BioFissativo Alta Adesione",
            ],
        )
        self.assertNotIn("Ruosteenestoaine Antiruggine Ecologico", self.names("PVC pohjamaali"))

    def test_task_queries(self):
        self.assertEqual(self.names("nikotiinitahrat"), ["Eristysmaali Decortina New"])
        self.assertEqual(self.names("homeenpoisto sisäseinä"), ["Homeenpoistoaine Sterylfix"])
        self.assertEqual(
            self.names("betonin vedenhylkivyys"),
            ["Väritön Impregnointiaine Betoncryll Idrorepellente"],
        )
        self.assertEqual(
            self.names("ruosteenestoaine"),
            ["Ruosteenestoaine Antiruggine Ecologico"],
        )

    def test_companion_is_ranked_after_primary_marmorino_products(self):
        names = self.names("marmoriino")
        self.assertEqual(names[:2], [
            "Kalkkipinnoite Marmorino Naturale",
            "Kalkkipinnoite Marmorino Naturale Fine",
        ])
        self.assertEqual(names[-1], "Suoja-Aine Protettivo Per Stucco E Marmorino")

    def test_unavailable_product_is_never_returned(self):
        self.products[0].available = False
        self.assertEqual(self.names("puulattian lakka"), [])

    def test_override_removes_unsupported_purpose_from_both_sources(self):
        source = {
            "keywords": {"purposes": ["suojaus", "nikotiinitahrat"]},
            "technical_filters": {
                "purposes": ["suojaus", "nikotiinitahrat"]
            },
        }
        merged = _merge_override(
            source, {"remove_purposes": ["nikotiinitahrat"]}
        )
        self.assertEqual(merged["keywords"]["purposes"], ["suojaus"])
        self.assertEqual(
            merged["technical_filters"]["purposes"], ["suojaus"]
        )


if __name__ == "__main__":
    unittest.main()
