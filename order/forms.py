from django import forms
from .models import Order
from django.contrib.auth.models import User

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'address', 'postal', 'city']

class OrderUpdateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['notes']
