from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from bookings.models import Booking
from itinerary.models import Itinerary
from reviews.models import Review

from .decorators import tourist_required
from .forms import TouristRegistrationForm
from .models import CustomUser


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = TouristRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = TouristRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def dashboard(request):
    """Central routing: send each role to its own dashboard."""
    user = request.user
    if user.is_staff:
        return redirect("admin_dashboard")
    if user.role == CustomUser.Role.VENDOR:
        return redirect("vendor_dashboard")
    return redirect("tourist_dashboard")


@tourist_required
def tourist_dashboard(request):
    user = request.user
    has_pending_application = hasattr(user, "vendor_profile")
    booking_count = Booking.objects.filter(tourist=user).count()
    review_count = Review.objects.filter(tourist=user).count()
    itinerary_count = Itinerary.objects.filter(tourist=user).count()
    return render(
        request,
        "accounts/tourist_dashboard.html",
        {
            "user": user,
            "has_pending_application": has_pending_application,
            "booking_count": booking_count,
            "review_count": review_count,
            "itinerary_count": itinerary_count,
        },
    )
