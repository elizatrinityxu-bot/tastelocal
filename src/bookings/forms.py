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
        error_messages = {
            "booking_date": {"required": "Please select a booking date and time."},
            "party_size":   {"required": "Please enter the number of guests."},
        }

    def __init__(self, *args, listing=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.listing = listing
        self.fields["booking_date"].input_formats = ["%Y-%m-%dT%H:%M"]

        # Apply Bootstrap form-control class to every widget.
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

        # Set frontend min/max on party_size so the browser pre-validates.
        if listing:
            self.fields["party_size"].widget.attrs.update({
                "min": 1,
                "max": listing.max_capacity,
            })
        else:
            self.fields["party_size"].widget.attrs["min"] = 1

    def clean_booking_date(self):
        booking_date = self.cleaned_data["booking_date"]

        # Must be in the future.
        if booking_date <= timezone.now():
            raise forms.ValidationError("Booking date must be in the future.")

        # Must fall within the vendor's opening hours.
        if self.listing:
            vendor = self.listing.vendor
            booking_time = booking_date.time()
            if booking_time < vendor.opening_time or booking_time >= vendor.closing_time:
                raise forms.ValidationError(
                    f"Booking time must be between "
                    f"{vendor.opening_time.strftime('%H:%M')} and "
                    f"{vendor.closing_time.strftime('%H:%M')}."
                )

        return booking_date

    def clean_party_size(self):
        party_size = self.cleaned_data["party_size"]

        if party_size < 1:
            raise forms.ValidationError("Party size must be at least 1.")

        if self.listing and party_size > self.listing.max_capacity:
            raise forms.ValidationError(
                f"Party size cannot exceed this listing's maximum capacity "
                f"of {self.listing.max_capacity}."
            )

        return party_size
