from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from users.views import ChangePasswordView

# Обработчик 404 ошибки
def custom_404_view(request, exception):
    return render(request, 'shop/base/404.html', status=404)

# Определяем handler404
handler404 = custom_404_view

urlpatterns = [
    #path('rosetta/', include('rosetta.urls')),
    path('admin/', admin.site.urls),
    path('google-shopping/', include('google_shopping.urls')),
    path('palvelut/', include('services.urls')),
    path('kurssit/', include('courses.urls')),
    path('user/', include('users.urls')),
    path('tinymce/', include('tinymce.urls')),
    path('user/password-change/', ChangePasswordView.as_view(), name='password_change'),
    path('cart/', include('cart.urls', namespace='cart')),
    path('order/', include('order.urls', namespace='order')),

    path('', include('config.legacy_urls')),

    path('', include('shop.urls', namespace='shop')),
    path('b2b/', include('b2b.urls', namespace='b2b')),
    path('blog/', include('blog.urls', namespace='blog')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
