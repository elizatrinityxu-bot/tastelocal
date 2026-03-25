from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import vendor_required
from bookings.models import Booking

from .forms import ReviewForm
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


@login_required
def submit_review(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, tourist=request.user)

    if request.method == "POST":
        if Review.objects.filter(tourist=request.user, booking=booking).exists():
            messages.warning(request, "You have already reviewed this booking.")
            return redirect("tourist_bookings")
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.tourist = request.user
            review.listing = booking.listing
            review.booking = booking
            review.save()
            messages.success(request, "Your review has been submitted. Thank you!")
        else:
            messages.warning(request, "Please enter a valid rating (1–5) and comment.")

    return redirect("tourist_bookings")


@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, tourist=request.user)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            review.rating = form.cleaned_data["rating"]
            review.review_text = form.cleaned_data["review_text"]
            review.save()
            messages.success(request, "Your review has been updated.")
        else:
            messages.warning(request, "Please enter a valid rating (1–5) and comment.")

    return redirect("tourist_bookings")


@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id, tourist=request.user)

    if request.method == "POST":
        review.delete()
        messages.success(request, "Your review has been deleted.")

    return redirect("tourist_bookings")


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
