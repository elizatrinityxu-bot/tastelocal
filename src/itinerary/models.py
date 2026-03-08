from django.conf import settings
from django.db import models


class Itinerary(models.Model):
    tourist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="itineraries",
    )
    title = models.CharField(max_length=255)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.title:
            self.title = f"My Food Tour \u2013 {self.date.day} {self.date.strftime('%b %Y')}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class ItineraryStop(models.Model):
    itinerary = models.ForeignKey(
        Itinerary,
        on_delete=models.CASCADE,
        related_name="stops",
    )
    listing = models.ForeignKey(
        "vendors.Listing",
        on_delete=models.CASCADE,
        related_name="itinerary_stops",
    )
    booking = models.OneToOneField(
        "bookings.Booking",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="itinerary_stop",
    )
    visit_order = models.IntegerField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["booking__booking_date", "visit_order"]

    def __str__(self):
        return f"Stop {self.visit_order} in '{self.itinerary.title}'"
