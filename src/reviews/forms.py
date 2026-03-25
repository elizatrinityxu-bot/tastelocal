from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    rating = forms.IntegerField(
        min_value=1,
        max_value=5,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 5}),
        label="Rating (1–5)",
    )
    review_text = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Share your experience…"}),
        label="Comment",
    )

    class Meta:
        model = Review
        fields = ["rating", "review_text"]
