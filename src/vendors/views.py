import math

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import tourist_required, vendor_required

from .forms import VendorApplicationForm
from .geocoding import geocode_address
from .models import Listing


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
    vendor = request.user.vendor_profile
    return render(request, "vendors/vendor_dashboard.html", {"vendor": vendor})


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
        Listing.objects.select_related("vendor").prefetch_related("images"),
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

    from_page = request.GET.get("from", "")
    back_lat  = request.GET.get("lat", "")
    back_lng  = request.GET.get("lng", "")

    return render(request, "vendors/listing_detail.html", {
        "listing": listing,
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

def browse_listings(request):
    """
    Shows all available listings.  Optionally filtered by:
      ?cuisine=MALAY   — one of the CuisineType values
      ?q=hawker        — keyword search on title
    """
    from .models import CuisineType

    cuisine_filter = request.GET.get("cuisine", "").upper()
    keyword = request.GET.get("q", "").strip()

    qs = (
        Listing.objects
        .filter(availability=True, vendor__is_active=True)
        .select_related("vendor")
        .prefetch_related("images")
        .order_by("cuisine_type", "title")
    )

    if cuisine_filter in CuisineType.values:
        qs = qs.filter(cuisine_type=cuisine_filter)

    if keyword:
        qs = qs.filter(title__icontains=keyword)

    return render(
        request,
        "vendors/browse_listings.html",
        {
            "listings": qs,
            "cuisine_types": CuisineType.choices,
            "active_cuisine": cuisine_filter,
            "keyword": keyword,
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
        {"results": results, "error": error, "user_lat": user_lat, "user_lng": user_lng},
    )
