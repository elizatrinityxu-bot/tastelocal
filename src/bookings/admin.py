from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("listing", "tourist", "status", "booking_date")
    list_filter = ("status", "booking_date")
    search_fields = ("tourist__username", "listing__title")
