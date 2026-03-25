from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.vendor_dashboard, name="vendor_dashboard"),
    path("listings/", views.vendor_listings, name="vendor_listings"),
    path("listings/new/", views.listing_create, name="listing_create"),
    path("listings/<int:pk>/edit/", views.listing_edit, name="listing_edit"),
    path("listings/<int:pk>/delete/", views.listing_delete, name="listing_delete"),
    path("apply/", views.apply_vendor, name="apply_vendor"),
    path("pending/", views.pending_vendor, name="pending_vendor"),
]
