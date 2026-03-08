from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import render

from .models import Itinerary, ItineraryStop


@login_required
def my_itineraries(request):
    stop_qs = (
        ItineraryStop.objects
        .select_related("listing", "booking")
        .order_by("booking__booking_date", "visit_order")
    )
    itineraries = (
        Itinerary.objects
        .filter(tourist=request.user)
        .prefetch_related(Prefetch("stops", queryset=stop_qs))
        .order_by("date")
    )

    # Annotate each itinerary's stops with end_time and overlap flag.
    for itin in itineraries:
        stops = list(itin.stops.all())

        # Compute start / end datetimes for each stop.
        for stop in stops:
            if stop.booking:
                stop.start_dt = stop.booking.booking_date
                stop.end_dt = stop.start_dt + timedelta(minutes=stop.listing.duration)
            else:
                stop.start_dt = None
                stop.end_dt = None

        # Detect overlaps: mark a stop if it starts before the previous one ends.
        overlapping_ids = set()
        for i in range(1, len(stops)):
            prev = stops[i - 1]
            curr = stops[i]
            if (
                prev.end_dt is not None
                and curr.start_dt is not None
                and curr.start_dt < prev.end_dt
            ):
                overlapping_ids.add(prev.id)
                overlapping_ids.add(curr.id)

        for stop in stops:
            stop.overlaps = stop.id in overlapping_ids

        # Attach annotated list so the template can iterate without re-querying.
        itin.annotated_stops = stops

    return render(request, "itinerary/my_itineraries.html", {"itineraries": itineraries})
