from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.decorators import vendor_required

from .models import Review


@login_required
def my_reviews(request):
    reviews = (
        Review.objects
        .filter(tourist=request.user)
        .select_related("listing", "listing__vendor")
        .order_by("-created_at")
    )
    return render(request, "reviews/my_reviews.html", {"reviews": reviews})


@vendor_required
def vendor_reviews(request):
    vendor = request.user.vendor_profile
    reviews = (
        Review.objects
        .filter(listing__vendor=vendor, is_approved=True)
        .select_related("listing", "tourist")
        .order_by("-created_at")
    )
    return render(request, "reviews/vendor_reviews.html", {
        "vendor": vendor,
        "reviews": reviews,
    })
