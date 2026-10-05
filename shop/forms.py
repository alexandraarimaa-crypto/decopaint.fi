from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['product', 'user', 'order', 'name', 'rating', 'title', 'text', 'image']

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.product = self.product
        instance.order = self.order
        if commit:
            instance.save()
        return instance


class ContactForm(forms.Form):
    email = forms.EmailField(required=True)
    title = forms.CharField(required=True)
    text = forms.CharField(widget=forms.Textarea, required=True)