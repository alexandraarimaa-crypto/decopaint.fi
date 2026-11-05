"""Exercise real blog routes without changing the isolated legacy URL suite."""
from django.urls import include, path

from config.test_urls import urlpatterns as existing_patterns

urlpatterns = [path("blog/", include("blog.urls")), *existing_patterns]
