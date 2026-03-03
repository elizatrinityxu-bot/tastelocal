from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Itinerary


@login_required
def my_itineraries(request):
    itineraries = (
        Itinerary.objects
        .filter(tourist=request.user)
        .prefetch_related("stops__listing")
        .order_by("-date")
    )
    return render(request, "itinerary/my_itineraries.html", {"itineraries": itineraries})
