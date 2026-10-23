from modeltranslation.translator import TranslationOptions, register

from .models import (
    Attribute,
    Category,
    Effect,
    Product,
    ProductDocument,
    ProductYoutubeLink,
    Slider,
    StoreSettings,
    Tag,
)


@register(StoreSettings)
class StoreSettingsTranslationOptions(TranslationOptions):
    fields = ("open_time", "terms", "top_bar", "company_terms")


@register(Slider)
class SliderTranslationOptions(TranslationOptions):
    fields = ("title", "info", "link_text")


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ("name", "title", "info", "keyword")


@register(Tag)
class TagTranslationOptions(TranslationOptions):
    # Tag names are internal unique keys used by existing links.
    fields = ("info",)


@register(Product)
class ProductTranslationOptions(TranslationOptions):
    # Product names intentionally remain unchanged in every language.
    fields = ("description", "tech_info", "properties")


@register(Effect)
class EffectTranslationOptions(TranslationOptions):
    fields = (
        "name",
        "application_method",
        "coverage",
        "tools_base",
        "tools_finish",
        "dilution",
    )


@register(ProductDocument)
class ProductDocumentTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(ProductYoutubeLink)
class ProductYoutubeLinkTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Attribute)
class AttributeTranslationOptions(TranslationOptions):
    fields = (
        "family",
        "purpose",
        "application",
        "color",
        "gloss",
        "sufficiency",
        "voc",
        "thinning",
        "density",
        "a_class",
        "epd",
        "ch2o",
        "haccp",
        "method",
        "primer",
        "ph",
        "abrasion_class",
    )
