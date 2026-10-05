from django.http import HttpResponse
from django.urls import include, path


def placeholder_view(request):
    return HttpResponse()


urlpatterns = [
    path("", include("config.legacy_urls")),
    path("cart/", include("cart.urls", namespace="cart")),
    path("user/", include("users.urls")),
    path("order/", include("order.urls", namespace="order")),
    path(
        "b2b/",
        include(([path("", placeholder_view, name="start")], "b2b"), namespace="b2b"),
    ),
    path(
        "blog/",
        include(
            ([path("", placeholder_view, name="blog_list")], "blog"),
            namespace="blog",
        ),
    ),
    path(
        "palvelut/",
        include(
            ([path("", placeholder_view, name="service_list")], "services"),
            namespace="services",
        ),
    ),
    path(
        "kurssit/",
        include(
            ([path("", placeholder_view, name="course_list")], "courses"),
            namespace="courses",
        ),
    ),
    path("", include("shop.urls", namespace="shop")),
]
