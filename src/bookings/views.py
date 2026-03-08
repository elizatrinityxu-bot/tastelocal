from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import tourist_or_vendor_required, tourist_required, vendor_required
from itinerary.models import Itinerary, ItineraryStop
from vendors.models import Listing

from .forms import BookingForm
from .models import Booking

# Permitted status transitions — vendors only.
# Tourists cannot trigger any transition.
VALID_TRANSITIONS = {
    Booking.Status.PENDING: {Booking.Status.CONFIRMED, Booking.Status.CANCELLED},
    Booking.Status.CONFIRMED: {Booking.Status.COMPLETED},
}


def _add_to_itinerary(booking):
    """Create an ItineraryStop for this booking, under the day's Itinerary."""
    date = booking.booking_date.date()
    itin, _ = Itinerary.objects.get_or_create(
        tourist=booking.tourist,
        date=date,
        defaults={"title": ""},  # auto-generated in Itinerary.save()
    )
    next_order = itin.stops.count() + 1
    ItineraryStop.objects.create(
        itinerary=itin,
        listing=booking.listing,
        booking=booking,
        visit_order=next_order,
        notes=booking.notes or "",
    )


def _remove_from_itinerary(booking):
    """Delete the ItineraryStop linked to this booking; prune empty itineraries."""
    try:
        stop = booking.itinerary_stop
    except ItineraryStop.DoesNotExist:
        return
    itin = stop.itinerary
    stop.delete()
    if not itin.stops.exists():
        itin.delete()


def _auto_expire(queryset):
    """
    Advance past bookings to their terminal status before display.
    PENDING + past → EXPIRED
    CONFIRMED + past → COMPLETED
    """
    now = timezone.now()
    past = queryset.filter(booking_date__lt=now)
    past.filter(status=Booking.Status.PENDING).update(status=Booking.Status.EXPIRED)
    past.filter(status=Booking.Status.CONFIRMED).update(status=Booking.Status.COMPLETED)


@tourist_or_vendor_required
def create_booking(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id, availability=True)

    if request.method == "POST":
        form = BookingForm(request.POST, listing=listing)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.tourist = request.user
            booking.listing = listing
            booking.status = Booking.Status.PENDING
            booking.save()
            _add_to_itinerary(booking)
            messages.success(
                request,
                "Booking submitted successfully. Your request is now pending vendor confirmation."
            )
            return redirect("tourist_bookings")
    else:
        form = BookingForm(listing=listing)

    return render(
        request,
        "bookings/booking_create.html",
        {"form": form, "listing": listing},
    )


@tourist_or_vendor_required
def tourist_bookings(request):
    _auto_expire(Booking.objects.filter(tourist=request.user))
    bookings = (
        Booking.objects.filter(tourist=request.user)
        .select_related("listing", "listing__vendor")
        .order_by("-created_at")
    )
    return render(request, "bookings/tourist_bookings.html", {"bookings": bookings})


@vendor_required
def vendor_bookings(request):
    vendor = request.user.vendor_profile
    _auto_expire(Booking.objects.filter(listing__vendor=vendor))
    bookings = (
        Booking.objects.filter(listing__vendor=vendor)
        .select_related("listing", "tourist")
        .order_by("-created_at")
    )
    return render(
        request,
        "bookings/vendor_bookings.html",
        {"bookings": bookings, "vendor": vendor},
    )


@tourist_or_vendor_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, tourist=request.user)
    cancellable = {Booking.Status.PENDING, Booking.Status.CONFIRMED}
    if request.method == "POST" and booking.status in cancellable:
        booking.status = Booking.Status.CANCELLED
        booking.save()
        _remove_from_itinerary(booking)
    return redirect("tourist_bookings")


@vendor_required
def update_booking_status(request, booking_id):
    vendor = request.user.vendor_profile
    # Scope to this vendor's listings only — prevents cross-vendor tampering.
    booking = get_object_or_404(Booking, id=booking_id, listing__vendor=vendor)

    if request.method == "POST":
        new_status = request.POST.get("status", "").upper()
        allowed = VALID_TRANSITIONS.get(booking.status, set())
        if new_status in allowed:
            booking.status = new_status
            booking.save()

    return redirect("vendor_bookings")
