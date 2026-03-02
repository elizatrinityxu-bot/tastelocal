from django import forms
from django.utils import timezone

from .models import Booking


class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["booking_date", "party_size", "notes"]
        widgets = {
            "booking_date": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, listing=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.listing = listing
        self.fields["booking_date"].input_formats = ["%Y-%m-%dT%H:%M"]

    def clean_booking_date(self):
        booking_date = self.cleaned_data["booking_date"]
        if booking_date <= timezone.now():
            raise forms.ValidationError("Booking date must be in the future.")
        return booking_date

    def clean_party_size(self):
        party_size = self.cleaned_data["party_size"]
        if self.listing and party_size > self.listing.max_capacity:
            raise forms.ValidationError(
                f"Party size cannot exceed this listing's capacity "
                f"of {self.listing.max_capacity}."
            )
        return party_size
