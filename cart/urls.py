from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='cart_detail'),
    path('checkout/', views.checkout, name='checkout'),
    path('add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('remove/<int:product_id>/<int:size_variant_id>/', views.cart_remove, name='cart_remove'),
    path('remove-selected/', views.cart_remove_selected, name='cart_remove_selected'),
    path('cart-clear/', views.cart_clear, name='cart_clear'),
    path('cart-update/', views.cart_update, name='cart_update'),
    path('remove-discount/', views.remove_discount, name='remove_discount'),
    path('update-shipping-method/', views.update_shipping_method, name='update_shipping_method'),
]

