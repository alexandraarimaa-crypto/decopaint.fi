from django import forms
from django.core.validators import FileExtensionValidator
from .models import CourseRegistration

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

class CourseRegistrationForm(forms.ModelForm):
    # Use the custom MultipleFileField
    images = MultipleFileField(
        label='Liitteet', 
        required=False, 
        widget=MultipleFileInput(attrs={'multiple': True, 'class': 'form-control'}),
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'pdf'])]
    )

    class Meta:
        model = CourseRegistration
        fields = ['name', 'email', 'phone', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nimesi'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Sähköpostiosoitteesi'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Puhelinnumerosi'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Viesti', 'rows': 5}),
        }
