from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = 'user'
urlpatterns = [
    path('', views.profile, name='profile'),
    path('orders/', views.order_history, name='order_history'),
    path('orders/<int:pk>/', views.order_details, name='order_details'),
    path('signup/', views.register, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('send_register_email/', views.send_register_email, name='send_register_email'),
    path('load_payment_details/<int:order_id>', views.load_payment_details, name='load_payment_details'),
]