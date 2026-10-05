from django import forms

PRODUCT_QUANTITY_CHOICES = [(i, str(i)) for i in range(1, 11)]

class CartAddProductForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, initial=1)
    update = forms.BooleanField(required=False, initial=False)
    size = forms.CharField(required=False, initial=None)
    color = forms.CharField(required=False, initial=None)
    grain = forms.CharField(required=False, initial=None)
    gloss = forms.CharField(required=False, initial=None)
    base = forms.CharField(required=False, initial=None)

class CouponForm(forms.Form):
    code = forms.CharField(label='Alennuskoodi')