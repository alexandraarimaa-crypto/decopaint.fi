from django import forms
from django.core.validators import FileExtensionValidator

class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = single_file_clean(data, initial)
        return result

class QuoteRequestForm(forms.Form):
    name = forms.CharField(label='Nimi', max_length=100, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nimesi'}))
    email = forms.EmailField(label='Sähköposti', required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Sähköpostiosoitteesi'}))
    phone = forms.CharField(label='Puhelinnumero', max_length=20, required=True, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Puhelinnumerosi'}))
    message = forms.CharField(label='Viesti', widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Kerro projektistasi...'}), required=True)
    
    # Use the custom MultipleFileField
    images = MultipleFileField(
        label='Liitä kuvia (valinnainen)', 
        required=False, 
        widget=MultipleFileInput(attrs={'multiple': True, 'class': 'form-control'}),
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]
    )
