from modeltranslation.translator import register, TranslationOptions
from .models import Slider

@register(Slider)
class SliderTranslationOptions(TranslationOptions):
    fields = ('title', 'info')
    populate_from = ('title', 'info',)