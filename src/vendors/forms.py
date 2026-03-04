from django import forms

from .models import Vendor


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
                attrs={"placeholder": "e.g. 123 Jalan Bukit Bintang, Kuala Lumpur, Malaysia"}
            ),
        }
