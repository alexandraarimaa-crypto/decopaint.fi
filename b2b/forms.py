from django import forms
from .models import CompanyApplication

class CompanyApplicationForm(forms.ModelForm):
    class Meta:
        model = CompanyApplication
        fields = ['first_name', 'last_name', 'position', 'email', 'phone', 'bill_address', 'bill_postal', 'bill_city', 'company', 'vat', 'text', 'reseller', 'invoicing', 'terms_accepted',]