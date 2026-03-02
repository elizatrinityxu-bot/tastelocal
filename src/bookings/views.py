from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import tourist_required, vendor_required
from vendors.models import Listing

from .forms import BookingForm
from .models import Booking

# Permitted status transitions — vendors only.
# Tourists cannot trigger any transition.
VALID_TRANSITIONS = {
    Booking.Status.PENDING: {Booking.Status.CONFIRMED, Booking.Status.CANCELLED},
    Booking.Status.CONFIRMED: {Booking.Status.COMPLETED},
}


@tourist_required
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
            return redirect("tourist_bookings")
    else:
        form = BookingForm(listing=listing)

    return render(
        request,
        "bookings/booking_create.html",
        {"form": form, "listing": listing},
    )


@tourist_required
def tourist_bookings(request):
    bookings = (
        Booking.objects.filter(tourist=request.user)
        .select_related("listing", "listing__vendor")
        .order_by("-created_at")
    )
    return render(request, "bookings/tourist_bookings.html", {"bookings": bookings})


@vendor_required
def vendor_bookings(request):
    vendor = request.user.vendor_profile
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
