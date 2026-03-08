from django.urls import path

from . import views

urlpatterns = [
    path("my/", views.my_reviews, name="my_reviews"),
    path("vendor/", views.vendor_reviews, name="vendor_reviews"),
]
