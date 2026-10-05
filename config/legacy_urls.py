from django.urls import path
from django.views.generic import RedirectView


def permanent_redirect(url):
    return RedirectView.as_view(url=url, permanent=True, query_string=True)


urlpatterns = [
    path("fi", permanent_redirect("/"), name="legacy_fi"),
    path("fi/", permanent_redirect("/"), name="legacy_fi_slash"),
    path("fi-fi/", permanent_redirect("/"), name="legacy_fi_fi"),
    path("fi/fi/", permanent_redirect("/"), name="legacy_fi_nested"),
    path("yhteystiedot", permanent_redirect("/contact/"), name="legacy_yhteystiedot"),
    path("contact-us", permanent_redirect("/contact/"), name="legacy_contact_us"),
    path("ota-yhteys", permanent_redirect("/contact/"), name="legacy_ota_yhteys"),
    path("ota-yhteytta", permanent_redirect("/contact/"), name="legacy_ota_yhteytta"),
    path("ota-yhteyttä", permanent_redirect("/contact/"), name="legacy_ota_yhteytta_unicode"),
    path("yhteys", permanent_redirect("/contact/"), name="legacy_yhteys"),
    path("product/1-primer/", permanent_redirect("/product/il-primer/"), name="legacy_1_primer"),
    path(
        "product/avf-plus-2k-lakka/",
        permanent_redirect("/product/avf-plus-opaco-ab-1-kg/"),
        name="legacy_avf_plus",
    ),
    path(
        "product/biomalta-extreme-media/",
        permanent_redirect("/product/biomalta-extreme/"),
        name="legacy_biomalta_extreme",
    ),
    path(
        "product/maalaussivellin-pettinato/",
        permanent_redirect("/catalog/tyokalut/"),
        name="legacy_pettinato",
    ),
    path(
        "product/sottosmalto-ecologico/",
        permanent_redirect("/catalog/pohjamaali-primer/"),
        name="legacy_sottosmalto",
    ),
]
