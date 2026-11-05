"""Blog metadata derived from visible content; no CMS writes or migrations."""

from html import unescape
from html.parser import HTMLParser
from urllib.parse import urlencode

from django.urls import reverse
from django.utils.translation import get_language

from shop.product_schema import absolute_product_image, json_for_script


DESCRIPTIONS = {
    "lasikuitutapetin-tasoitus-kalkkipinnoite": {
        "fi": "Lasikuitutapetin tasoitus: milloin tapetin voi ylitasoittaa, miten pohja valmistellaan ja millainen maali- tai kalkkipinta sopii viimeistelyyn?",
        "sv": "Spackla glasfibertapet: när kan tapeten bredspacklas, hur förbereds underlaget och vilken färg eller kalkyta passar som avslutning?",
        "en": "Skimming fibreglass wallpaper: when to keep the wallpaper, how to prepare the substrate and which paint or lime finish to choose.",
    },
    "ottocento": {
        "fi": "OIKOS Ottocento -efektimaali: vertaile samettisia pintoja, levitystekniikoita ja menekkejä. Katso työohjeet ja tarvittavat tuotteet.",
        "sv": "OIKOS Ottocento effektfärg: jämför sammetslika ytor, appliceringstekniker och materialåtgång. Se arbetsanvisningar och produkter.",
        "en": "OIKOS Ottocento effect paint: compare velvety finishes, application techniques and coverage. Explore instructions and the products you need.",
    },
    "kalkkimaali-marmorino-venetsialainen-stucco": {
        "fi": "Kalkkimaali, Marmorino vai venetsialainen stucco? Vertaa pintojen ulkonäköä, levitystä ja käyttökohteita sekä löydä sopiva OIKOS-pinnoite.",
        "sv": "Kalkfärg, Marmorino eller venetiansk puts? Jämför utseende, applicering och användning och hitta en lämplig OIKOS-yta för ditt projekt.",
        "en": "Lime paint, Marmorino or Venetian plaster? Compare finishes, application methods and uses to choose a suitable OIKOS surface for your project.",
    },
    "kuinka-paljon-maalia-tarvitsen": {
        "fi": "Laske maalin menekki pinta-alan, kerrosten ja riittoisuuden perusteella. Katso laskuesimerkit ja vinkit sopivan pakkauskoon valintaan.",
        "sv": "Beräkna färgåtgång med hjälp av yta, antal strykningar och täckförmåga. Se räkneexempel och tips för att välja rätt förpackningsstorlek.",
        "en": "Calculate paint quantity from wall area, coats and coverage. See worked examples and tips for choosing a suitable pack size for your project.",
    },
}


UI = {
    "fi": {
        "list_title": "Maalaus- ja sisustusoppaat",
        "list_intro": "Vertaile pintoja, laske materiaalimäärä ja löydä ohjeet omaan projektiisi.",
        "list_description": "Ohjeita maalien ja sisustuspinnoitteiden valintaan, menekin laskemiseen ja pintojen toteutukseen. Löydä projektiisi sopivat OIKOS-tuotteet.",
        "help_title": "Valitaan materiaalit sinun projektiisi",
        "help_text": "Kerro pinta-ala, nykyinen alusta ja toivottu lopputulos. Autamme valitsemaan sopivat tuotteet ja pakkauskoot.",
        "help_button": "Pyydä apua materiaalivalintaan",
        "related_title": "Lue myös projektisi suunnitteluun",
        "product_guides_title": "Oppaat tuotteen valintaan ja käyttöön",
        "enquiry_title": "Apua oman projektisi materiaalivalintaan",
        "topic": "Aihe",
        "enquiry_instructions": "Täydennä viestiin pinta-ala, alusta ja toivottu lopputulos. Voit muokata viestiä ennen lähettämistä.",
        "message_label": "Viesti",
    },
    "sv": {
        "list_title": "Guider för målning och inredning",
        "list_intro": "Jämför ytor, beräkna materialåtgång och hitta råd för ditt projekt.",
        "list_description": "Guider för att välja färg och dekorativa ytor, beräkna materialåtgång och planera arbetet. Hitta lämpliga OIKOS-produkter för ditt projekt.",
        "help_title": "Vi hjälper dig välja material till ditt projekt",
        "help_text": "Beskriv ytan, det befintliga underlaget och önskat resultat. Vi hjälper dig välja lämpliga produkter och förpackningsstorlekar.",
        "help_button": "Be om hjälp med materialval",
        "related_title": "Läs också inför ditt projekt",
        "product_guides_title": "Guider för val och användning av produkten",
        "enquiry_title": "Hjälp med materialval för ditt projekt",
        "topic": "Ämne",
        "enquiry_instructions": "Komplettera med yta, underlag och önskat resultat. Du kan ändra meddelandet innan du skickar det.",
        "message_label": "Meddelande",
    },
    "en": {
        "list_title": "Painting and decorative finish guides",
        "list_intro": "Compare finishes, estimate materials and find guidance for your project.",
        "list_description": "Guides to choosing paints and decorative finishes, estimating material quantities and planning application. Find suitable OIKOS products for your project.",
        "help_title": "Choose materials for your project with us",
        "help_text": "Tell us the area, existing substrate and desired result. We will help you choose suitable products and pack sizes.",
        "help_button": "Ask for help choosing materials",
        "related_title": "More guides for planning your project",
        "product_guides_title": "Guides to choosing and using this product",
        "enquiry_title": "Help choosing materials for your project",
        "topic": "Topic",
        "enquiry_instructions": "Add the area, substrate and desired result to your message. You can edit it before sending.",
        "message_label": "Message",
    },
}


def ui_text():
    return UI.get(language(), UI["fi"])


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.hidden += 1
        if not self.hidden:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.hidden = max(0, self.hidden - 1)
        self.parts.append(" ")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def plain_text(value):
    parser = _Text()
    parser.feed(str(value or ""))
    return " ".join(unescape("".join(parser.parts)).split())


def _excerpt(value, limit=170):
    text = plain_text(value)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"


def language():
    return (get_language() or "fi").split("-")[0]


def metadata(post, request):
    lang = language()
    description = DESCRIPTIONS.get(post.slug, {}).get(lang)
    if not description:
        description = _excerpt(post.content) or _excerpt(post.title)
    canonical = request.build_absolute_uri(post.get_absolute_url())
    image = absolute_product_image(request, post)
    data = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": plain_text(post.title),
        "description": description,
        "url": canonical,
        "mainEntityOfPage": canonical,
        "datePublished": post.created_at.isoformat(),
        "inLanguage": lang,
        "publisher": {"@type": "Organization", "name": "Deco Paint Finland Oy"},
    }
    if image:
        data["image"] = [image]
    return {
        "description": description,
        "canonical": canonical,
        "image": image,
        "schema_json": json_for_script(data),
    }


def enquiry_url(post):
    return reverse("shop:contact") + "?" + urlencode({"guide": post.slug}) + "#project-enquiry"
