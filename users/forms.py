from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms
from .models import CustomUser
from order.models import Order

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'password1', 'password2')

class CustomUserChangeForm(UserChangeForm):
    first_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(max_length=100, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    company = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    vat = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    address = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    postal = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    city = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    bill_address = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    bill_postal = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    bill_city = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone', 'company', 'vat', 'address', 'postal', 'city', 'bill_address', 'bill_postal', 'bill_city']
