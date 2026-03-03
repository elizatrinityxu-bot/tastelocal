from django.contrib.auth.decorators import login_required
from django.shortcuts import render

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
