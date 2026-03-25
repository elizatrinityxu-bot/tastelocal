import math

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Q
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import tourist_required, vendor_required
from core.models import WishlistItem

from .forms import ListingForm, VendorApplicationForm
from .geocoding import geocode_address
from .models import Listing


def _saved_listing_ids(user):
    if not user.is_authenticated:
        return set()
    return set(WishlistItem.objects.filter(user=user).values_list("listing_id", flat=True))


# ---------------------------------------------------------------------------
# Haversine formula — great-circle distance between two lat/lng points (km).
# ---------------------------------------------------------------------------

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0  # Earth's mean radius in kilometres
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Vendor dashboard
# ---------------------------------------------------------------------------

@vendor_required
def vendor_dashboard(request):
    from bookings.models import Booking
    from itinerary.models import Itinerary
    from reviews.models import Review

    vendor = request.user.vendor_profile
    booking_count = Booking.objects.filter(listing__vendor=vendor).count()
    listing_count = vendor.listings.count()
    review_count = Review.objects.filter(listing__vendor=vendor, is_approved=True).count()

    tourist_booking_count = Booking.objects.filter(tourist=request.user).count()
    tourist_review_count = Review.objects.filter(tourist=request.user).count()
    tourist_itinerary_count = Itinerary.objects.filter(tourist=request.user).count()
    has_tourist_activity = tourist_booking_count > 0 or tourist_review_count > 0 or tourist_itinerary_count > 0

    return render(request, "vendors/vendor_dashboard.html", {
        "vendor": vendor,
        "booking_count": booking_count,
        "listing_count": listing_count,
        "review_count": review_count,
        "has_tourist_activity": has_tourist_activity,
    })


# ---------------------------------------------------------------------------
# Vendor listings
# ---------------------------------------------------------------------------

@vendor_required
def vendor_listings(request):
    vendor = request.user.vendor_profile
    listings = (
        vendor.listings
        .prefetch_related("images")
        .order_by("title")
    )
    return render(request, "vendors/vendor_listings.html", {
        "vendor": vendor,
        "listings": listings,
    })


# ---------------------------------------------------------------------------
# Listing edit / delete
# ---------------------------------------------------------------------------

@vendor_required
def listing_edit(request, pk):
    vendor = request.user.vendor_profile
    listing = get_object_or_404(Listing, pk=pk, vendor=vendor)
    if request.method == "POST":
        form = ListingForm(request.POST, instance=listing)
        if form.is_valid():
            form.save()
            return redirect("vendor_listings")
    else:
        form = ListingForm(instance=listing)
    return render(request, "vendors/listing_edit.html", {"form": form, "listing": listing})


@vendor_required
def listing_delete(request, pk):
    vendor = request.user.vendor_profile
    listing = get_object_or_404(Listing, pk=pk, vendor=vendor)
    if request.method == "POST":
        title = listing.title
        listing.delete()
        messages.success(request, f'"{title}" has been deleted.')
    return redirect("vendor_listings")


# ---------------------------------------------------------------------------
# Vendor application flow
# ---------------------------------------------------------------------------

@tourist_required
def apply_vendor(request):
    """
    Tourists submit a vendor application here.
    - Prevents duplicate applications via the OneToOne guard.
    - Geocodes the submitted address to derive latitude/longitude.
    - Does NOT change user.role — admin does that after approval.
    - Sets is_approved=False unconditionally.
    """
    if hasattr(request.user, "vendor_profile"):
        return redirect("pending_vendor")

    if request.method == "POST":
        form = VendorApplicationForm(request.POST)
        if form.is_valid():
            vendor = form.save(commit=False)
            vendor.user = request.user
            vendor.is_approved = False

            try:
                lat, lng = geocode_address(vendor.address)
            except ValueError as exc:
                form.add_error("address", str(exc))
                return render(request, "vendors/apply_vendor.html", {"form": form})

            vendor.latitude = lat
            vendor.longitude = lng
            vendor.save()
            return redirect("pending_vendor")
    else:
        form = VendorApplicationForm()

    return render(request, "vendors/apply_vendor.html", {"form": form})


@login_required
def pending_vendor(request):
    # If the vendor has since been approved, skip the waiting room
    # and send them straight to the dashboard router.
    if hasattr(request.user, "vendor_profile"):
        if request.user.vendor_profile.is_approved:
            return redirect("dashboard")
    return render(request, "vendors/pending_vendor.html")


# ---------------------------------------------------------------------------
# Listing detail
# ---------------------------------------------------------------------------

def listing_detail(request, pk):
    listing = get_object_or_404(
        Listing.objects.select_related("vendor").prefetch_related("images", "stops"),
        pk=pk,
    )
    reviews = list(
        listing.reviews.filter(is_approved=True).select_related("tourist").order_by("-created_at")
    )
    review_count = len(reviews)
    avg_rating = (
        round(sum(r.rating for r in reviews) / review_count, 1)
        if review_count else None
    )
    avg_rating_int = int(avg_rating) if avg_rating else 0
    review_slides = [reviews[i:i + 2] for i in range(0, len(reviews), 2)]

    similar = (
        Listing.objects
        .filter(
            availability=True,
            cuisine_type=listing.cuisine_type,
            vendor__is_approved=True,
            vendor__is_active=True,
        )
        .exclude(pk=listing.pk)
        .annotate(avg_rating=Avg("reviews__rating", filter=Q(reviews__is_approved=True)))
        .select_related("vendor")
        .prefetch_related("images")
        .order_by("?")[:3]
    )

    from_page = request.GET.get("from", "")
    back_lat  = request.GET.get("lat", "")
    back_lng  = request.GET.get("lng", "")

    return render(request, "vendors/listing_detail.html", {
        "listing": listing,
        "similar": similar,
        "reviews": reviews,
        "review_slides": review_slides,
        "review_count": review_count,
        "avg_rating": avg_rating,
        "avg_rating_int": avg_rating_int,
        "from_page": from_page,
        "back_lat": back_lat,
        "back_lng": back_lng,
    })


# ---------------------------------------------------------------------------
# Browse listings (cuisine / keyword filter — no geolocation required)
# ---------------------------------------------------------------------------

_PRICE_RANGES = {
    "under-50":  (None, 50),
    "50-100":    (50,  100),
    "100-200":   (100, 200),
    "200-plus":  (200, None),
}


def browse_listings(request):
    """
    Shows all available listings.  Optionally filtered by:
      ?cuisine=MALAY     — one of the CuisineType values
      ?q=hawker          — keyword search on title + description
      ?price=50-100      — price range bucket
      ?min_rating=4      — minimum average approved-review rating
    """
    from .models import CuisineType

    cuisine_filter = request.GET.get("cuisine", "").upper()
    keyword       = request.GET.get("q", "").strip()
    price_range   = request.GET.get("price", "")
    min_rating    = request.GET.get("min_rating", "")

    qs = (
        Listing.objects
        .filter(availability=True, vendor__is_active=True)
        .annotate(avg_rating=Avg("reviews__rating", filter=Q(reviews__is_approved=True)))
        .select_related("vendor")
        .prefetch_related("images")
        .order_by("cuisine_type", "title")
    )

    if cuisine_filter in CuisineType.values:
        qs = qs.filter(cuisine_type=cuisine_filter)

    if keyword:
        qs = qs.filter(Q(title__icontains=keyword) | Q(description__icontains=keyword))

    if price_range in _PRICE_RANGES:
        low, high = _PRICE_RANGES[price_range]
        if low is not None:
            qs = qs.filter(price__gte=low)
        if high is not None:
            qs = qs.filter(price__lt=high)

    if min_rating:
        try:
            qs = qs.filter(avg_rating__gte=float(min_rating))
        except ValueError:
            min_rating = ""

    return render(
        request,
        "vendors/browse_listings.html",
        {
            "listings": qs,
            "cuisine_types": CuisineType.choices,
            "active_cuisine": cuisine_filter,
            "keyword": keyword,
            "price_range": price_range,
            "min_rating": min_rating,
            "saved_listing_ids": _saved_listing_ids(request.user),
        },
    )


# ---------------------------------------------------------------------------
# Nearby listings
# ---------------------------------------------------------------------------

def nearby_listings(request):
    """
    Returns available listings ordered by distance from a user-supplied
    coordinate pair (lat, lng query parameters).

    Distance is calculated using the Haversine formula and displayed in km.
    """
    error = None
    results = []
    user_lat = request.GET.get("lat", "")
    user_lng = request.GET.get("lng", "")

    if user_lat or user_lng:
        try:
            user_lat_f = float(user_lat)
            user_lng_f = float(user_lng)
        except (TypeError, ValueError):
            error = "Please provide valid numeric values for lat and lng."
            return render(
                request,
                "vendors/nearby_listings.html",
                {"error": error, "results": results},
            )

        listings = (
            Listing.objects.filter(availability=True, vendor__is_active=True)
            .select_related("vendor")
            .prefetch_related("images")
        )

        for listing in listings:
            vendor = listing.vendor
            if vendor.latitude is None or vendor.longitude is None:
                continue
            distance = _haversine(
                user_lat_f,
                user_lng_f,
                float(vendor.latitude),
                float(vendor.longitude),
            )
            results.append({
                "listing": listing,
                "vendor": vendor,
                "distance_km": round(distance, 2),
            })

        results.sort(key=lambda x: x["distance_km"])

    return render(
        request,
        "vendors/nearby_listings.html",
        {
            "results": results,
            "error": error,
            "user_lat": user_lat,
            "user_lng": user_lng,
            "saved_listing_ids": _saved_listing_ids(request.user),
        },
    )
