from django.urls import path
from . import views

app_name = 'b2b'

urlpatterns = [
    path('', views.b2b_view, name='start'),
]