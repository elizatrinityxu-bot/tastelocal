from django.urls import path

from . import views

urlpatterns = [
    path("create/<int:listing_id>/", views.create_booking, name="booking_create"),
    path("my/", views.tourist_bookings, name="tourist_bookings"),
    path("vendor/", views.vendor_bookings, name="vendor_bookings"),
    path("<int:booking_id>/update/", views.update_booking_status, name="booking_update_status"),
]
