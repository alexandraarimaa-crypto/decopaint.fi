from django.db import models
from tinymce.models import HTMLField
from users.models import CustomUser

class CompanyApplication(models.Model):
    STATUS_CHOICES = [
        ('new', 'Uusi'),
        ('accepted', 'Hyväksytty'),
        ('canceled', 'Hylätty'),
    ]
    status = models.CharField('Tila', max_length=20, choices=STATUS_CHOICES, default='new')
    user = models.ForeignKey(CustomUser, related_name='users_applications', on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField('Etunimi', max_length=130, blank=False)
    last_name = models.CharField('Sukunimi', max_length=130, blank=False)
    position = models.CharField('Asema yrityksessä', max_length=130, blank=False, default="")
    email = models.EmailField(blank=False)
    phone = models.CharField('Puhelinnumero', max_length=130, blank=False, default="")
    company = models.CharField('Yritys', max_length=230, blank=False)
    vat = models.CharField('Y-tunnus', max_length=30, blank=False)
    text = HTMLField('Hakemusteksti', blank=True)
    sended = models.DateTimeField('Hakemus jätetty', auto_now_add=True, null=False)
    updated = models.DateTimeField('Päivitetty', auto_now=True, null=False)
    reseller = models.BooleanField('Jälleenmyynti', default=False)
    invoicing = models.BooleanField('Laskutus', default=False)
    bill_address = models.CharField('Laskutusosoite', max_length=200, null=True, blank=True, default='')
    bill_postal = models.CharField('Postinumero', max_length=200, null=True, blank=True, default='')
    bill_city = models.CharField('Postitoimipaikka', max_length=200, null=True, blank=True, default='')
    terms_accepted = models.BooleanField('Ehdot hyväksytty', default=False, blank=False)

    def __str__(self):
        return f'Companies applications'
    
    class Meta:
        verbose_name = 'B2B hakemus'
        verbose_name_plural = 'B2B hakemukset'