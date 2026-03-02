from django.contrib import admin

from .models import Itinerary, ItineraryStop


class ItineraryStopInline(admin.TabularInline):
    model = ItineraryStop
    extra = 1
    ordering = ("visit_order",)


@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ("title", "tourist", "date", "created_at")
    search_fields = ("title", "tourist__username")
    inlines = [ItineraryStopInline]


@admin.register(ItineraryStop)
class ItineraryStopAdmin(admin.ModelAdmin):
    list_display = ("itinerary", "listing", "visit_order")
    ordering = ("itinerary", "visit_order")
