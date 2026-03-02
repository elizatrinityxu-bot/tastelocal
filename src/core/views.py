from django.shortcuts import render

from vendors.models import CuisineType, Listing


def index(request):
    featured = (
        Listing.objects
        .filter(availability=True)
        .select_related("vendor")
        .prefetch_related("images")
        .order_by("?")[:6]
    )
    context = {
        "featured": featured,
        "cuisine_types": CuisineType.choices,
    }
    return render(request, "core/index.html", context)
