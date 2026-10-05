"""Source-grounded SEO metadata for the first Finnish P0 release.

This module intentionally contains no database writes and no product claims
outside the approved PDF-backed SEO plan.  It also centralises canonical URL
construction so tracking, filter and product option parameters cannot become
indexable duplicates.
"""

from urllib.parse import urlencode

from django.utils.html import strip_tags
from django.utils.text import Truncator


DEFAULT_DESCRIPTION = (
    "OIKOS-maalit ja sisustuspinnoitteet kotiin ja ammattilaisille. "
    "Tutustu tuotteisiin, teknisiin tietoihin ja asiantuntija-apuun."
)

HOME_SEO = {
    "title": "OIKOS-maalit ja sisustuspinnoitteet | Deco Paint",
    "description": (
        "Osta OIKOS-sisustusmaalit, kalkkimaalit, sisustuslaastit ja "
        "julkisivupinnoitteet. Tuotekohtaiset ohjeet, tekniset PDF:t ja "
        "asiantuntija-apu."
    ),
    "h1": "OIKOS-maalit ja sisustuspinnoitteet kotiin ja ammattilaisille",
}

CATALOG_SEO = {
    "title": "OIKOS-maalit, pinnoitteet ja työkalut | Deco Paint",
    "description": (
        "Selaa Deco Paintin OIKOS-tuotteita. Rajaa tuotteet käyttökohteen, "
        "alustan ja tuotetyypin mukaan ja tarkista tekniset tiedot ennen valintaa."
    ),
    "h1": "OIKOS-maalit, pinnoitteet ja tarvikkeet",
}

CATEGORY_SEO = {
    "sisustusmaali": {
        "title": "Sisustusmaalit ja sisäseinämaalit | OIKOS",
        "description": (
            "Tutustu OIKOS-sisustusmaaleihin. Vertaa käyttökohdetta, kiiltoa, "
            "riittoisuutta ja teknisiä tietoja ja valitse kohteeseen sopiva "
            "sisäseinämaali."
        ),
        "h1": "Sisustusmaalit sisäseinille",
        "intro": (
            "Valitse sisustusmaali huoneen, alustan ja halutun pinnan mukaan. "
            "Tarkista aina tuotteen teknisestä PDF:stä sopiva pohjustus, "
            "riittoisuus ja levitysohje ennen työn aloittamista."
        ),
    },
    "kalkkimaali": {
        "title": "Kalkkimaalit seinille | OIKOS",
        "description": (
            "Vertaa OIKOS-kalkkimaaleja Pittura Alla Calce Verona, Sterylcalce "
            "ja Tiepolo Opaco. Tarkista alusta, pohjustus, riittoisuus ja levitysohje."
        ),
        "h1": "Kalkkimaalit seinäpinnoille",
        "intro": (
            "Kalkkimaali ja kalkkipinnoite ovat eri tuoteryhmiä. Vertaile tällä "
            "sivulla kalkkimaaleja ja varmista tuotekohtaisesta teknisestä "
            "PDF:stä alusta, pohjustus ja levitys."
        ),
    },
    "sisustuslaasti": {
        "title": "Sisustuslaastit ja koristepinnoitteet | OIKOS",
        "description": (
            "Tutustu OIKOS-sisustuslaasteihin ja -pinnoitteisiin. Vertaa "
            "materiaalia, alustaa, työvälineitä, pohjustusta ja teknisiä käyttöohjeita."
        ),
        "h1": "Sisustuslaastit ja pinnoitteet seinille",
        "intro": (
            "Sisustuslaastin valintaan vaikuttavat alusta, haluttu rakenne ja "
            "levitystapa. Tuotekortit ja tekniset PDF:t kertovat järjestelmään "
            "kuuluvat pohjusteet, työvälineet ja mahdollisen suojauksen."
        ),
    },
    "koristemaali": {
        "title": "Koristemaalit seinille | OIKOS",
        "description": (
            "Löydä OIKOS-koristemaali elävään seinäpintaan. Vertaa Multidecor-, "
            "Encanto- ja muita vaihtoehtoja sekä niiden pohjusteita ja levitystapoja."
        ),
        "h1": "Koristemaalit yksilöllisiin seinäpintoihin",
        "intro": (
            "Koristemaalilla voidaan toteuttaa erilaisia näkyviä pintavaikutelmia. "
            "Valitse tuote halutun lopputuloksen mukaan ja noudata aina kyseisen "
            "tuotteen teknistä ohjetta."
        ),
    },
    "efektimaali": {
        "title": "Efektimaalit ja efektiseinät | OIKOS",
        "description": (
            "Tutustu OIKOS-efektimaaleihin, työvälineisiin ja vahvistettuihin "
            "levitystapoihin. Valitse haluttuun pintaan teknisesti sopiva tuote."
        ),
        "h1": "Efektimaalit näyttäviin seinäpintoihin",
        "intro": (
            "Efektiseinän lopputulos syntyy tuotteen, pohjan ja työvälineen "
            "yhdistelmästä. Tarkista tuotekortista ja teknisestä PDF:stä juuri "
            "valitulle tuotteelle vahvistettu levitystapa."
        ),
    },
    "kalkkipinnoite": {
        "title": "Kalkkipinnoitteet ja Marmorino | OIKOS",
        "description": (
            "Tutustu Marmorino Naturale- ja muihin OIKOS-kalkkipinnoitteisiin. "
            "Tarkista alusta, pohjuste, suojaus, riittoisuus ja tekninen PDF."
        ),
        "h1": "Kalkkipinnoitteet ja Marmorino-pinnat",
        "intro": (
            "Kalkkipinnoitteiden rakenne, riittoisuus ja työvaiheet ovat "
            "tuotekohtaisia. Vertaa vaihtoehtoja ja varmista oikea pohjustus sekä "
            "mahdollinen suojaus tuotteen virallisesta teknisestä PDF:stä."
        ),
    },
    "ulkomaalit": {
        "title": "Julkisivumaalit ja ulkopinnoitteet | OIKOS",
        "description": (
            "OIKOS-julkisivumaalit ja ulkopinnoitteet rappaus-, betoni- ja "
            "sementtipinnoille. Valitse järjestelmä alustan ja teknisten tietojen mukaan."
        ),
        "h1": "Julkisivumaalit ja ulkopinnoitteet",
        "intro": (
            "Valitse ulkopinnan tuote alustan ja nykyisen pintakäsittelyn mukaan. "
            "Tällä sivulla näkyvät tuotteet, joiden ulkokäyttö on vahvistettu; "
            "tarkista lopullinen järjestelmä aina tuotteen teknisestä PDF:stä."
        ),
    },
    "siloksan-mineraalimaali": {
        "title": "Siloksaanimaalit julkisivuille | OIKOS",
        "description": (
            "Vertaa OIKOS-siloksaani- ja siloksan-mineraalimaaleja ulkoseinille. "
            "Tarkista hyväksytty alusta, pohjuste, riittoisuus ja levitysolosuhteet."
        ),
        "h1": "Siloksaanimaalit ulkoseinille",
    },
    "pohjamaali-primer": {
        "title": "Pohjamaalit ja tartuntapohjamaalit | OIKOS",
        "description": (
            "Valitse OIKOS-pohjamaali alustan ja pintatuotteen mukaan. Vertaa "
            "tartuntaa, imevyyden tasausta, levitystä ja hyväksyttyä jatkokäsittelyä."
        ),
        "h1": "Pohjamaalit eri alustoille",
    },
    "homeenestomaali": {
        "title": "Homeenestomaalit sisäseinille | OIKOS",
        "description": (
            "Tutustu OIKOS-homeenestomaaleihin ja tarkista tuotekohtainen "
            "käyttökohde, alustan valmistelu, pohjustus ja tekninen ohje."
        ),
        "h1": "Homeenestomaalit sisäseinille",
    },
    "kaakelimaali": {
        "title": "Kaakelimaalit seinille ja lattioille | OIKOS",
        "description": (
            "Tutustu OIKOS-kaakelimaaliin sisätilojen keraami-, betoni-, kivi- "
            "ja terrakottapinnoille. Tarkista käyttörajat ja tekninen ohje."
        ),
        "h1": "Kaakelimaalit sisätiloihin",
    },
    "patterimaali": {
        "title": "Patterimaalit lämpöpattereille | OIKOS",
        "description": (
            "Tutustu OIKOS-patterimaaliin ja tarkista metallipinnan valmistelu, "
            "levitystapa, kuivuminen ja tekninen käyttöohje."
        ),
        "h1": "Patterimaalit lämpöpattereille",
    },
}

PRODUCT_SEO = {
    "marmorino-naturale": {
        "title": "Marmorino Naturale kalkkipinnoite | OIKOS",
        "description": (
            "OIKOS Marmorino Naturale on kalkkipohjainen sisä- ja ulkoseinien "
            "pinnoite. Katso riittoisuus, Consolidante Calce -pohjustus ja suojaus PDF:stä."
        ),
        "h1": "Kalkkipinnoite Marmorino Naturale",
    },
    "cemento-materico": {
        "title": "Cemento Materico betoniefekti seinään | OIKOS",
        "description": (
            "OIKOS Cemento Materico sisäseinien koristeellisiin betoniefekteihin. "
            "Katso Il Primer, työvälineet, suojaus, riittoisuus ja tekninen PDF."
        ),
        "h1": "Cemento Materico -pinnoite betoniefektiin",
    },
    "ecosmalto-per-ceramica": {
        "title": "Kaakelimaali seinille ja lattioille | OIKOS",
        "description": (
            "Ecosmalto per Ceramica sisätilojen kaakeli-, betoni-, kivi- ja "
            "terrakottapinnoille. Ei jatkuvaan vesikosketukseen. Katso järjestelmä ja ohje."
        ),
        "h1": "Kaakelimaali Ecosmalto per Ceramica",
    },
    "ecoprotettivo-parquet": {
        "title": "Parkettilakka puulattialle | OIKOS",
        "description": (
            "Ecoprotettivo Parquet on puulattioiden suojalakka. Tarkista "
            "Turapori-pohjustus, puun kosteus, riittoisuus, kuivuminen ja levitysohje PDF:stä."
        ),
        "h1": "Parkettilakka Ecoprotettivo Parquet",
    },
    "decortina-new": {
        "title": "Eristysmaali nikotiini- ja savutahroille | OIKOS",
        "description": (
            "Decortina New sisäseinien savu-, noki- ja nikotiinitahroille. Katso "
            "pinnan valmistelu, Crilux/Neofix-pohjustus, riittoisuus ja kuivuminen."
        ),
        "h1": "Eristysmaali Decortina New",
    },
}

# These tag URLs compete with stronger category URLs.  Redirects are activated
# only in this release's view code and are covered by regression tests.
TAG_CATEGORY_REDIRECTS = {
    "sisustusmaalit": "sisustusmaali",
    "sisustuslaastit": "sisustuslaasti",
    "koristemaalit": "koristemaali",
    "ulkomaalit": "ulkomaalit",
}

# The exterior assortment currently exists as a high-signal tag but lacks a
# canonical category record.  The P0 landing page is rendered code-only, so no
# production/staging database mutation is needed.
VIRTUAL_CATEGORY_TAGS = {"ulkomaalit": "ulkomaalit"}


def build_canonical(request, keep_query=()):
    """Return an absolute canonical with only explicitly approved parameters."""

    base_url = request.build_absolute_uri(request.path)
    query = []
    for key in keep_query:
        value = request.GET.get(key)
        if value and value not in {"1", 1}:
            query.append((key, value))
    if not query:
        return base_url
    return f"{base_url}?{urlencode(query)}"


def category_seo(slug, fallback_name=""):
    if slug in CATEGORY_SEO:
        return dict(CATEGORY_SEO[slug])
    name = (fallback_name or "OIKOS-tuotteet").strip()
    return {
        "title": Truncator(f"{name} | OIKOS").chars(60),
        "description": Truncator(
            f"Tutustu OIKOS-tuoteryhmään {name}. Vertaa tuotteita ja tarkista "
            "tuotekohtaiset tekniset tiedot ennen valintaa."
        ).chars(170),
        "h1": name,
    }


def product_seo(slug, fallback_name="", fallback_description=""):
    if slug in PRODUCT_SEO:
        return dict(PRODUCT_SEO[slug])
    name = (fallback_name or "OIKOS-tuote").strip()
    description = Truncator(strip_tags(fallback_description or "")).chars(165)
    return {
        "title": Truncator(f"{name} | OIKOS").chars(60),
        "description": description or DEFAULT_DESCRIPTION,
        "h1": name,
    }
