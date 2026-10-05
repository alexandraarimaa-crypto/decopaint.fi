from django.urls import path
from . import views
from pk_paytrail.views import create_payment, payment_success, payment_cancel, get_payment_methods

app_name = 'order'

urlpatterns = [
    path('create_payment/', create_payment, name='create_payment'),
    path('payment_success/', payment_success, name='payment_success'),
    path('payment_cancel/', payment_cancel, name='payment_cancel'),
    path('get_payment_methods/', get_payment_methods, name='get_payment_methods'),
]