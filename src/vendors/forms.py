from django import forms

from .models import Listing, Vendor


class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ["title", "description", "price", "duration", "max_capacity", "cuisine_type", "availability"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"rows": 4, "class": "form-control"}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "duration": forms.NumberInput(attrs={"class": "form-control"}),
            "max_capacity": forms.NumberInput(attrs={"class": "form-control"}),
            "cuisine_type": forms.Select(attrs={"class": "form-select"}),
            "availability": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class VendorApplicationForm(forms.ModelForm):
    class Meta:
        model = Vendor
        # latitude and longitude are intentionally excluded — they are derived
        # automatically from the address via geocoding on form submission.
        fields = ["name", "description", "cuisine_types", "address"]
        labels = {
            "name": "Business Name",
        }
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "e.g. Ramirez Culinary Tours"}
            ),
            "description": forms.Textarea(attrs={"rows": 4}),
            "address": forms.TextInput(
                attrs={"placeholder": "e.g. 123 Orchard Road, Singapore 238888"}
            ),
        }
