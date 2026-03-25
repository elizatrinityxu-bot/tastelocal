from bookings.models import Booking
from itinerary.models import Itinerary
from reviews.models import Review


def tourist_activity(request):
    """Inject has_tourist_activity for vendor users so the navbar can conditionally
    show the Tourist View link without needing per-view context updates."""
    if not request.user.is_authenticated:
        return {}
    if getattr(request.user, "role", None) != "VENDOR":
        return {}
    has_tourist_activity = (
        Booking.objects.filter(tourist=request.user).exists()
        or Review.objects.filter(tourist=request.user).exists()
        or Itinerary.objects.filter(tourist=request.user).exists()
    )
    return {"has_tourist_activity": has_tourist_activity}
