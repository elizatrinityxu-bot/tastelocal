from django.urls import path

from . import views

urlpatterns = [
    path("nearby/", views.nearby_listings, name="nearby_listings"),
    path("browse/", views.browse_listings, name="browse_listings"),
    path("<int:pk>/", views.listing_detail, name="listing_detail"),
]
