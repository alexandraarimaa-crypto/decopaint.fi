from django.contrib import admin
from .models import Service, QuoteRequest, QuoteRequestFile, ServiceAdditionalImage

class QuoteRequestFileInline(admin.TabularInline):
    model = QuoteRequestFile
    extra = 0

class ServiceAdditionalImageInline(admin.TabularInline):
    model = ServiceAdditionalImage
    extra = 1

@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'service', 'email', 'created_at')
    list_filter = ('service', 'created_at')
    inlines = [QuoteRequestFileInline]
    readonly_fields = ('created_at',)

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title', 'content')
    inlines = [ServiceAdditionalImageInline]
