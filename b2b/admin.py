from django.contrib import admin
from .models import CompanyApplication

@admin.register(CompanyApplication)
class CompanyApplicationAdmin(admin.ModelAdmin):
    list_display = ['company', 'status', 'email', 'first_name', 'last_name', 'sended', 'updated', 'reseller', 'invoicing']
    readonly_fields = ['user', 'first_name', 'last_name', 'email', 'phone', 'position', 'company', 'vat', 'bill_address', 'bill_postal', 'bill_city', 'text', 'sended',  'updated', 'reseller', 'invoicing', 'terms_accepted']
    search_fields = ['company', 'email', 'first_name', 'last_name',]
    list_filter = ['status', 'reseller', 'invoicing',]