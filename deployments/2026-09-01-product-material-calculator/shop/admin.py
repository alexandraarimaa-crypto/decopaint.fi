from django.contrib import admin
from django import forms
from django.contrib.auth.models import Group
from django.contrib.auth.admin import GroupAdmin
from .models import Effect, Category, Product, Variant, ShippingCost, Coupon, Tax, Multiplier, GroupSettings, StoreSettings, Tag, ProductImage, Attribute, RelatedProduct, Review, RecentProductView, Slider, ProductDocument, ProductYoutubeLink, ProductMaterialCalculatorPackage
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from solo.admin import SingletonModelAdmin
from django_admin_inline_paginator.admin import TabularInlinePaginated
from django.forms import ModelForm
from modeltranslation.admin import TranslationAdmin
from .models import PriceUpdateFile, Variant
from .tasks import update_variant_prices
from django_q.tasks import async_task
from mptt.admin import MPTTModelAdmin
from django.utils.safestring import mark_safe
from django.utils.html import format_html

admin.site.site_header = 'Decopaint admin'

class PriceUpdateFileAdmin(admin.ModelAdmin):
    list_display = ('uploaded_at',)
    actions = ['process_price_updates']

    def process_price_updates(self, request, queryset):
        for obj in queryset:
            async_task(update_variant_prices, obj.file.path)
        self.message_user(request, "Hintapäivitystehtävät on käynnistetty.")
    process_price_updates.short_description = "Käsittele valitut hintapäivitystiedostot"

admin.site.register(PriceUpdateFile, PriceUpdateFileAdmin)


@admin.register(StoreSettings)
class StoreSettingsAdmin(SingletonModelAdmin):
    list_display = ['id', 'weight_based_enabled', 'postnord_lokero_enabled', 'postnord_kotiinkuljetus_enabled', 'pickup_enabled', 'free_shipping_threshold', 'free_shipping_method']
    
    def has_add_permission(self, request):
        if self.model.objects.count() >= 1:
            return False
        return super().has_add_permission(request)
    
    fieldsets = (
        ('Perusasetukset', {
            'fields': ('email', 'open_time', 'terms', 'top_bar', 'company_terms')
        }),
        ('Toimitusasetukset - Painoperusteinen', {
            'fields': ('weight_based_enabled',)
        }),
        ('Toimitusasetukset - Postnord palvelupiste', {
            'fields': ('postnord_lokero_enabled', 'postnord_lokero_price')
        }),
        ('Toimitusasetukset - Postnord Kotiinkuljetus', {
            'fields': ('postnord_kotiinkuljetus_enabled', 'postnord_kotiinkuljetus_price')
        }),
        ('Toimitusasetukset - Nouto myymälästä', {
            'fields': ('pickup_enabled',)
        }),
        ('Ilmaisen toimituksen asetukset', {
            'fields': ('free_shipping_threshold', 'free_shipping_method')
        }),
    )

class GroupSettingsForm(forms.ModelForm):
    class Meta:
        model = GroupSettings
        fields = '__all__'

class GroupSettingsInline(admin.StackedInline):
    model = GroupSettings
    form = GroupSettingsForm

class RelatedProductInline(admin.TabularInline):
    model = RelatedProduct
    fk_name = 'product'
    extra = 1

# Unregister the default GroupAdmin to re-register with the custom modifications
admin.site.unregister(Group)

@admin.register(Group)
class CustomGroupAdmin(GroupAdmin):
    inlines = [GroupSettingsInline]

@admin.register(Slider)
class SliderAdmin(TranslationAdmin):
    list_display = ['title', 'order', 'active']
    list_editable = ['order',]

@admin.register(Effect)
class EffectAdmin(admin.ModelAdmin):
    list_display = ['product', 'application_method', 'coverage', 'dilution']
    search_fields = ['application_method', 'coverage', 'dilution']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['created', 'product', 'user', 'order', 'title', 'rating', 'active']
    list_editable = ['active',]
    list_filter = ['active', 'product', 'rating']
    search_fields = ['product', 'user',]

@admin.register(RecentProductView)
class RecentProductViewAdmin(admin.ModelAdmin):
    list_display = ['viewed_at', 'user', 'product',]

@admin.register(ShippingCost)
class ShippingCostAdmin(admin.ModelAdmin):
    list_display = ['weight_from', 'weight_to', 'price']
    search_fields = ['weight_from', 'weight_to', 'price']

@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ['name', 'rate']
    search_fields = ['name']

@admin.register(Multiplier)
class MultiplierAdmin(admin.ModelAdmin):
    list_display = ['multi']
    search_fields = ['multi']

@admin.register(Category)
class CategoryAdmin(MPTTModelAdmin):
    list_display = ['name', 'slug', 'parent', 'active']
    search_fields = ['name', 'slug']
    list_filter = ['active']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount', 'amount', 'min_purchase', 'single_use', 'is_valid']
    list_filter = ['active', 'single_use', 'start_date', 'end_date']
    filter_horizontal = ['used_by']

class AttributeAdmin(admin.ModelAdmin):
    list_display = ['product']

class EffectInline(admin.TabularInline):
    model = Effect
    extra = 1

class VariantInline(TabularInlinePaginated):
    model = Variant
    extra = 1
    ordering = ['item_code']
    fields = ['active', 'item_description', 'price', 'color1', 'color2', 'base', 'size', 'grain', 'gloss', 'weight', 'barcode', 'image', 'thumbnail']
    readonly_fields = ['barcode', 'item_code',]
    show_change_link = True 
    per_page = 100
    extra = 0
    
    class Media:
        css = {
            'all': ('assets/css/custom_admin.css',),
        }

class VariantAdminForm(ModelForm):
    class Meta:
        model = Variant
        exclude = []

class TagInline(admin.TabularInline):
    model = Product.tags.through
    extra = 0

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0

class AttributeInline(admin.TabularInline):
    model = Attribute
    extra = 0

class ActiveCategoryFilter(admin.SimpleListFilter):
    title = _('Active Categories')
    parameter_name = 'active_category'

    def lookups(self, request, model_admin):
        return (
            ('active', _('Active')),
            ('all', _('All')),
        )

    def queryset(self, request, queryset):
        # Определение типа модели, к которой применяется фильтр
        model = queryset.model

        if self.value() == 'active':
            # Если модель Product, фильтруем по активным категориям Product
            if model == Product:
                return queryset.filter(category__active=True)
            # Если модель Variant, фильтруем по активным категориям Product,
            # используя связь с Product
            elif model == Variant:
                return queryset.filter(product__category__active=True)
        elif self.value() == 'all':
            return queryset

    def default_value(self):
        return 'active'

    def choices(self, changelist):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == str(lookup),
                'query_string': changelist.get_query_string({self.parameter_name: lookup}),
                'display': title,
            }

    def value(self):
        value = super().value()
        if value in ('', None):
            value = self.default_value()
        return value

class ProductDocumentInline(admin.TabularInline):
    model = ProductDocument
    extra = 1

class ProductYoutubeLinkInline(admin.TabularInline):
    model = ProductYoutubeLink
    extra = 1

class ProductMaterialCalculatorPackageInline(admin.TabularInline):
    model = ProductMaterialCalculatorPackage
    extra = 0
    fields = ['active', 'variant', 'label', 'amount', 'unit', 'order']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'variant':
            object_id = request.resolver_match.kwargs.get('object_id') if request.resolver_match else None
            if object_id:
                kwargs['queryset'] = Variant.objects.filter(product_id=object_id).order_by('item_code', 'size', 'id')
            else:
                kwargs['queryset'] = Variant.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'price',
        'multiplier',
        'discount_percentage',
        'material_calculator_manual_enabled',
        'material_calculator_coverage_min',
        'material_calculator_coverage_max',
        'material_calculator_unit',
        'available',
        'updated',
    ]
    list_filter = [
        'material_calculator_manual_enabled',
        'available',
        'category',
        'discount_percentage',
        'created',
        'updated',
    ]
    filter_horizontal = ('category',)
    search_fields = ['name', 'description']
    list_editable = [
        'material_calculator_manual_enabled',
        'material_calculator_coverage_min',
        'material_calculator_coverage_max',
        'material_calculator_unit',
        'available',
    ]
    prepopulated_fields = {'slug': ('name',)}
    exclude = ('tags',)
    list_per_page = 150
    inlines = [AttributeInline, ProductMaterialCalculatorPackageInline, ProductImageInline, RelatedProductInline, TagInline, ProductDocumentInline, ProductYoutubeLinkInline, EffectInline]
    actions = ['assign_category_to_products']  # Register custom action

    def assign_category_to_products(self, request, queryset):
        return assign_category_to_products(self, request, queryset)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('category').distinct()
    
# Custom admin action to assign products to a category by category ID
def assign_category_to_products(modeladmin, request, queryset):
    category_id = 18  # Set the category ID you want to assign the products to (e.g., category with ID=1)
    
    # Get the category object
    try:
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        modeladmin.message_user(request, "Category with ID {} does not exist.".format(category_id), level='error')
        return

    # Add the selected category to each product's category
    for product in queryset:
        product.category.add(category)

    modeladmin.message_user(request, "Selected products have been assigned to the category: {}".format(category.name))


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug',]

class RelatedProductAdmin(admin.ModelAdmin):
    list_display = ['product', 'related_product']
    search_fields = ['product__name', 'related_product__name']

class ActiveCategoryFilter(admin.SimpleListFilter):
    title = _('Tuote')
    parameter_name = 'active_category'

    def lookups(self, request, model_admin):
        active_products = Product.objects.filter(category__active=True).distinct()
        return (
            (product.id, product.name) for product in active_products
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(product_id=self.value())

    def default_value(self):
        return 'active'

class BaseFilter(admin.SimpleListFilter):
    title = _('Pohja')
    parameter_name = 'base'

    def lookups(self, request, model_admin):
        if request.GET.get('active_category'):
            product_id = request.GET.get('active_category')
            queryset = Variant.objects.filter(product_id=product_id).values_list('base', 'base').distinct()
            return queryset

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(base=value)

class SizeFilter(admin.SimpleListFilter):
    title = _('Koko')
    parameter_name = 'size'

    def lookups(self, request, model_admin):
        if request.GET.get('active_category'):
            product_id = request.GET.get('active_category')
            queryset = Variant.objects.filter(product_id=product_id).values_list('size', 'size').distinct()
            return queryset

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(size=value)

class GrainFilter(admin.SimpleListFilter):
    title = _('Raekoko')
    parameter_name = 'grain'

    def lookups(self, request, model_admin):
        if request.GET.get('active_category'):
            product_id = request.GET.get('active_category')
            queryset = Variant.objects.filter(product_id=product_id).values_list('grain', 'grain').distinct()
            return queryset

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(grain=value)

class GlossFilter(admin.SimpleListFilter):
    title = _('Kiiltoaste')
    parameter_name = 'gloss'

    def lookups(self, request, model_admin):
        if request.GET.get('active_category'):
            product_id = request.GET.get('active_category')
            queryset = Variant.objects.filter(product_id=product_id).values_list('gloss', 'gloss').distinct()
            return queryset

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(gloss=value)

class Color1Filter(admin.SimpleListFilter):
    title = _('Väri 1')
    parameter_name = 'color1'

    def lookups(self, request, model_admin):
        if request.GET.get('active_category'):
            product_id = request.GET.get('active_category')
            queryset = Variant.objects.filter(product_id=product_id).exclude(color1='').values_list('color1', 'color1').distinct()
            return queryset

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(color1=value)

class Color2Filter(admin.SimpleListFilter):
    title = _('Väri 2')
    parameter_name = 'color2'

    def lookups(self, request, model_admin):
        if request.GET.get('active_category'):
            product_id = request.GET.get('active_category')
            queryset = Variant.objects.filter(product_id=product_id).exclude(color2='').values_list('color2', 'color2').distinct()
            return queryset

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return queryset.filter(color2=value)
@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'active', 'item_code', 'item_description_short', 
        'size', 'display_color_with_preview', 'base', 'grain', 'gloss', 
        'price', 'order_item_badge'
    ]
    list_editable = ['size', 'base', 'grain', 'gloss', 'active', 'price']
    list_filter = [
        ActiveCategoryFilter, 'order_item', BaseFilter, SizeFilter, 
        GrainFilter, GlossFilter, Color1Filter, Color2Filter, 'product'
    ]
    search_fields = [
        'color1', 'color2', 'barcode', 'item_code', 
        'item_description', 'product__name'
    ]
    list_per_page = 50
    list_select_related = ['product']
    ordering = ['product__name', 'item_code']
    actions = ['make_order_item', 'make_stock_item', 'make_inactive', 'make_active']
    
    # Добавляем фильтр по цене
    list_filter.append(('price', admin.EmptyFieldListFilter))
    
    # Поля для быстрого редактирования в списке
    def get_list_editable(self, request):
        if request.user.is_superuser:
            return ['size', 'base', 'grain', 'gloss', 'active', 'price', 'order_item']
        return ['size', 'base', 'grain', 'gloss', 'active', 'price']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')
    
    def display_color_with_preview(self, obj):
        """Display color information with visual preview"""
        color_info = []
        
        if obj.color1:
            # Для Color1 показываем название и иконку изображения
            color_info.append(
                f'<span title="Color1: {obj.color1}">🎨 {obj.color1}</span>'
            )
        
        if obj.color2:
            # Для Color2 показываем RGB значение и цветной квадратик
            if obj.r is not None and obj.g is not None and obj.b is not None:
                color_box = f'<span style="display: inline-block; width: 12px; height: 12px; background: rgb({obj.r},{obj.g},{obj.b}); border: 1px solid #ccc; margin-right: 5px;"></span>'
                color_info.append(
                    f'<span title="Color2: {obj.color2} (RGB: {obj.r},{obj.g},{obj.b})">{color_box}{obj.color2}</span>'
                )
            else:
                color_info.append(f'RGB: {obj.color2}')
        
        if not color_info:
            return "-"
        
        return mark_safe(' / '.join(color_info))
    display_color_with_preview.short_description = 'Väri'
    display_color_with_preview.admin_order_field = 'color1'
    
    def item_description_short(self, obj):
        """Shortened item description for better display"""
        if obj.item_description:
            if len(obj.item_description) > 50:
                return f"{obj.item_description[:50]}..."
            return obj.item_description
        return "-"
    item_description_short.short_description = 'Kuvaus'
    item_description_short.admin_order_field = 'item_description'
    
    def item_code(self, obj):
        """Display item code with copy functionality"""
        if obj.item_code:
            return format_html(
                '<span title="Kopioi koodi" style="cursor: pointer;" onclick="navigator.clipboard.writeText(\'{}\')">{}</span>',
                obj.item_code,
                obj.item_code
            )
        return "-"
    item_code.short_description = 'Tuotekoodi'
    
    def order_item_badge(self, obj):
        """Display order item status as badge"""
        if obj.order_item:
            return mark_safe('<span style="color: orange;">● Tilaus</span>')
        else:
            return mark_safe('<span style="color: green;">● Varasto</span>')
    order_item_badge.short_description = 'Tilaustyyppi'
    
    def price(self, obj):
        """Display price with currency"""
        if obj.price:
            return f"{obj.price:.2f}€"
        return "-"
    price.short_description = 'Hinta'
    
    # Улучшенные действия
    def make_order_item(self, request, queryset):
        updated = queryset.update(order_item=True)
        self.message_user(request, f"{updated} tuotetta muutettu tilaustuotteiksi")
    make_order_item.short_description = "Muuta valitut tilaustuotteiksi"
    
    def make_stock_item(self, request, queryset):
        updated = queryset.update(order_item=False)
        self.message_user(request, f"{updated} tuotetta muutettu varastotuotteiksi")
    make_stock_item.short_description = "Muuta valitut varastotuotteiksi"
    
    def make_inactive(self, request, queryset):
        updated = queryset.update(active=False)
        self.message_user(request, f"{updated} tuotetta passivoitu")
    make_inactive.short_description = "Passivoi valitut tuotteet"
    
    def make_active(self, request, queryset):
        updated = queryset.update(active=True)
        self.message_user(request, f"{updated} tuotetta aktivoitu")
    make_active.short_description = "Aktivoi valitut tuotteet"
    
    # Добавляем кастомный CSS для улучшения внешнего вида
    class Media:
        css = {
            'all': ('admin/css/variant_admin.css',)
        }
    
    # Улучшенная форма редактирования
    fieldsets = (
        ('Perustiedot', {
            'fields': ('product', 'item_code', 'item_description', 'barcode', 'price')
        }),
        ('Värit', {
            'fields': ('color1', 'color2', 'r', 'g', 'b', 'hue', 'image', 'thumbnail')
        }),
        ('Tekniset tiedot', {
            'fields': ('size', 'base', 'grain', 'gloss', 'customs_code', 'weight')
        }),
        ('Tila', {
            'fields': ('active', 'order_item')
        }),
    )
    
    # Автозаполнение для связанных полей
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "product":
            kwargs["queryset"] = Product.objects.all().order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
