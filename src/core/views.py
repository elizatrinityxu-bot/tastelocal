from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from reviews.models import Review
from vendors.models import CuisineType, Listing, Vendor

from .models import WishlistItem


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _saved_listing_ids(user):
    """Return a set of listing PKs saved by the user, or empty set for anon."""
    if not user.is_authenticated:
        return set()
    return set(
        WishlistItem.objects.filter(user=user).values_list("listing_id", flat=True)
    )


# ---------------------------------------------------------------------------
# Public index
# ---------------------------------------------------------------------------

def index(request):
    featured = (
        Listing.objects
        .filter(availability=True, vendor__is_active=True)
        .select_related("vendor")
        .prefetch_related("images")
        .order_by("?")[:6]
    )
    popular = (
        Listing.objects
        .filter(availability=True, vendor__is_approved=True, vendor__is_active=True)
        .annotate(
            review_count=Count("reviews", filter=Q(reviews__is_approved=True)),
            avg_rating=Avg("reviews__rating", filter=Q(reviews__is_approved=True)),
        )
        .select_related("vendor")
        .prefetch_related("images")
        .order_by("-review_count", "-pk")[:6]
    )
    context = {
        "featured": featured,
        "popular": popular,
        "cuisine_types": CuisineType.choices,
        "saved_listing_ids": _saved_listing_ids(request.user),
    }
    return render(request, "core/index.html", context)


# ---------------------------------------------------------------------------
# Wishlist
# ---------------------------------------------------------------------------

@login_required
def wishlist_toggle(request, listing_id):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    listing = get_object_or_404(Listing, pk=listing_id)
    item, created = WishlistItem.objects.get_or_create(
        user=request.user, listing=listing
    )
    if not created:
        item.delete()
        saved = False
    else:
        saved = True
    return JsonResponse({"saved": saved})


@login_required
def my_wishlist(request):
    items = (
        WishlistItem.objects
        .filter(user=request.user)
        .select_related("listing", "listing__vendor")
        .prefetch_related("listing__images")
        .order_by("-created_at")
    )
    listings = [item.listing for item in items]
    saved_listing_ids = {listing.id for listing in listings}
    return render(request, "core/my_wishlist.html", {
        "listings": listings,
        "saved_listing_ids": saved_listing_ids,
    })


# ---------------------------------------------------------------------------
# Staff-only guard
# ---------------------------------------------------------------------------

def staff_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        if not request.user.is_staff:
            return redirect("index")
        return view_func(request, *args, **kwargs)
    return _wrapped


# ---------------------------------------------------------------------------
# Admin Dashboard Overview
# ---------------------------------------------------------------------------

@staff_required
def admin_dashboard(request):
    context = {
        "total_vendors": Vendor.objects.count(),
        "pending_vendors": Vendor.objects.filter(is_approved=False).count(),
        "inactive_vendors": Vendor.objects.filter(is_active=False).count(),
        "total_reviews": Review.objects.count(),
        "hidden_reviews": Review.objects.filter(is_approved=False).count(),
    }
    return render(request, "core/admin_dashboard.html", context)


# ---------------------------------------------------------------------------
# Admin Review Management
# ---------------------------------------------------------------------------

@staff_required
def admin_reviews(request):
    status_filter = request.GET.get("status", "")
    reviews = (
        Review.objects
        .select_related("tourist", "listing", "listing__vendor")
        .order_by("-created_at")
    )
    if status_filter == "hidden":
        reviews = reviews.filter(is_approved=False)
    return render(request, "core/admin_reviews.html", {
        "reviews": reviews,
        "status_filter": status_filter,
    })


@staff_required
def admin_review_action(request, pk):
    if request.method != "POST":
        return redirect("admin_reviews")

    review = get_object_or_404(Review, pk=pk)
    action = request.POST.get("action")

    if action == "approve":
        review.is_approved = True
        review.save(update_fields=["is_approved"])
        messages.success(request, f"Review #{pk} approved.")
    elif action == "hide":
        review.is_approved = False
        review.save(update_fields=["is_approved"])
        messages.success(request, f"Review #{pk} hidden.")
    elif action == "delete":
        review.delete()
        messages.success(request, f"Review #{pk} deleted.")

    return redirect("admin_reviews")


# ---------------------------------------------------------------------------
# Admin Vendor Management
# ---------------------------------------------------------------------------

@staff_required
def admin_vendors(request):
    status_filter = request.GET.get("status", "")
    vendors = Vendor.objects.select_related("user").annotate(listing_count=Count("listings")).order_by("-created_at")
    if status_filter == "pending":
        vendors = vendors.filter(is_approved=False)
    elif status_filter == "inactive":
        vendors = vendors.filter(is_active=False)
    return render(request, "core/admin_vendors.html", {
        "vendors": vendors,
        "status_filter": status_filter,
    })


@staff_required
def admin_vendor_action(request, pk):
    if request.method != "POST":
        return redirect("admin_vendors")

    vendor = get_object_or_404(Vendor, pk=pk)
    action = request.POST.get("action")

    if action == "approve":
        vendor.is_approved = True
        vendor.save(update_fields=["is_approved"])
        messages.success(request, f"Vendor \"{vendor.name}\" approved.")
    elif action == "activate":
        vendor.is_active = True
        vendor.save(update_fields=["is_active"])
        messages.success(request, f"Vendor \"{vendor.name}\" activated.")
    elif action == "deactivate":
        vendor.is_active = False
        vendor.save(update_fields=["is_active"])
        messages.success(request, f"Vendor \"{vendor.name}\" deactivated.")

    return redirect("admin_vendors")
