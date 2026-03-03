from functools import wraps

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from reviews.models import Review
from vendors.models import CuisineType, Listing, Vendor


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
    context = {
        "featured": featured,
        "cuisine_types": CuisineType.choices,
    }
    return render(request, "core/index.html", context)


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
    vendors = Vendor.objects.select_related("user").order_by("-created_at")
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

    if action == "activate":
        vendor.is_active = True
        vendor.save(update_fields=["is_active"])
        messages.success(request, f"Vendor \"{vendor.name}\" activated.")
    elif action == "deactivate":
        vendor.is_active = False
        vendor.save(update_fields=["is_active"])
        messages.success(request, f"Vendor \"{vendor.name}\" deactivated.")

    return redirect("admin_vendors")
