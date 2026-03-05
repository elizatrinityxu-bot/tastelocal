"""
Geocoding utility using OpenStreetMap Nominatim via geopy.
No API key required.
"""

from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim


def geocode_address(address: str) -> tuple[float, float]:
    """
    Derive (latitude, longitude) from a plain-text address string.

    Returns:
        (latitude, longitude) as floats.

    Raises:
        ValueError with a user-friendly message when the address cannot be
        resolved or the geocoding service is unavailable.
    """
    geolocator = Nominatim(user_agent="tastelocal_vendor_app", timeout=10)

    try:
        location = geolocator.geocode(address)
    except GeocoderTimedOut:
        raise ValueError(
            "The geocoding service timed out. Please try again in a moment."
        )
    except GeocoderServiceError:
        raise ValueError(
            "The geocoding service is temporarily unavailable. Please try again later."
        )

    if location is None:
        raise ValueError(
            "Address could not be found. Please enter a more specific address "
            "(include city, state, or country)."
        )

    return location.latitude, location.longitude

