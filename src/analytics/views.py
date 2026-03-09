from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.utils import timezone

from bookings.models import Booking
from core.views import staff_required
from reviews.models import Review
from vendors.models import Vendor


@staff_required
def analytics_dashboard(request):
    # ── Summary metrics ──────────────────────────────────────────
    total_vendors = Vendor.objects.count()
    pending_vendors = Vendor.objects.filter(is_approved=False).count()
    total_bookings = Booking.objects.count()
    total_reviews = Review.objects.count()
    hidden_reviews = Review.objects.filter(is_approved=False).count()

    # ── Bookings per month (last 12 months) ───────────────────────
    twelve_months_ago = timezone.now().replace(day=1) - timezone.timedelta(days=365)
    monthly_qs = (
        Booking.objects
        .filter(created_at__gte=twelve_months_ago)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )

    chart_labels = [entry["month"].strftime("%b %Y") for entry in monthly_qs]
    chart_data = [entry["count"] for entry in monthly_qs]

    context = {
        "total_vendors": total_vendors,
        "pending_vendors": pending_vendors,
        "total_bookings": total_bookings,
        "total_reviews": total_reviews,
        "hidden_reviews": hidden_reviews,
        "chart_labels": chart_labels,
        "chart_data": chart_data,
    }
    return render(request, "analytics/dashboard.html", context)
