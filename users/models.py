from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] 
    username = models.CharField(max_length=150, default='')
    email = models.EmailField(unique=False)
    first_name = models.CharField(max_length=200, blank=True, default='')
    last_name = models.CharField(max_length=200, blank=True, default='')
    phone = models.CharField(max_length=200, blank=True, default='')
    company = models.CharField(max_length=200, blank=True, default='')
    vat = models.CharField(max_length=200, blank=True, default='')
    address = models.CharField(max_length=200, blank=True, default='')
    postal = models.CharField(max_length=200, blank=True, default='')
    city = models.CharField(max_length=200, blank=True, default='')
    bill_address = models.CharField(max_length=200, blank=True, default='')
    bill_postal = models.CharField(max_length=200, blank=True, default='')
    bill_city = models.CharField(max_length=200, blank=True, default='')