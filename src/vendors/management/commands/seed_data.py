"""
Management command: seed_data
Usage: python manage.py seed_data

Populates the database with realistic tourism food experience data.
Existing seed data (identified by the 'seed_' username prefix) is
cleared before new records are inserted.  All writes are wrapped in
a single transaction — an error rolls everything back cleanly.
"""

import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from faker import Faker

from accounts.models import CustomUser
from bookings.models import Booking
from itinerary.models import Itinerary, ItineraryStop
from reviews.models import Review
from vendors.models import CuisineType, Listing, ListingImage, Vendor

fake = Faker()

# ── Constants ────────────────────────────────────────────────────────────────

SEED_PREFIX = "seed_"
VENDOR_COUNT = 10
TOURIST_COUNT = 10
LISTING_COUNT = 50
BOOKING_COUNT = 60
REVIEW_COUNT = 100
ITINERARY_COUNT = 10

CUISINE_VALUES = CuisineType.values   # ['CHINESE', 'MALAY', ...]

# ── Singapore bounding box ───────────────────────────────────────────────────
# Lat 1.25–1.45, Lng 103.75–104.00 as specified.
# Approximate diagonal spread: ~25 km — vendor-to-vendor distances stay
# within the 0.2–15 km realistic range for central Singapore districts.

LAT_MIN = Decimal("1.2500")
LAT_MAX = Decimal("1.4500")
LNG_MIN = Decimal("103.7500")
LNG_MAX = Decimal("104.0000")

# ── Domain data ──────────────────────────────────────────────────────────────

VENDOR_SUFFIXES = [
    "Food Experiences", "Culinary Tours", "Heritage Walks",
    "Food Adventures", "Cultural Tastings", "Gastro Tours",
    "Food Stories", "Hawker Guides", "Culinary Journeys", "Food Trails",
]

SG_AREAS = [
    "Chinatown", "Little India", "Kampong Glam", "Tanjong Pagar",
    "Bugis", "Tiong Bahru", "Geylang", "Katong", "Joo Chiat",
    "Queenstown", "Bishan", "Ang Mo Kio", "Bedok", "Tampines",
    "Dempsey Hill", "Holland Village", "Clarke Quay", "Boat Quay",
]

# Tourism food experience names keyed by cuisine type
EXPERIENCE_NAMES = {
    "CHINESE": [
        "Chinatown Night Food Trail",
        "Traditional Dim Sum Morning Experience",
        "Heritage Kopitiam Culture Tour",
        "Teochew Hawker Heritage Walk",
        "Cantonese Wok Skills Masterclass",
        "Chinatown Breakfast Discovery",
        "Bak Kut Teh Heritage Journey",
        "Chinese New Year Feast Experience",
        "Old Hokkien Street Food Trail",
        "Roast Meats & Rice Culture Walk",
    ],
    "MALAY": [
        "Kampong Malay Culinary Journey",
        "Heritage Kampong Food Experience",
        "Traditional Nasi Lemak Cooking Class",
        "Geylang Supper Tour Experience",
        "Authentic Rendang Masterclass",
        "Malay Heritage Trail & Tasting",
        "Village Warung Culture Experience",
        "Rempah Spice Blending Workshop",
        "Kampong Glam Food & Culture Walk",
        "Malay Wedding Feast Experience",
    ],
    "INDIAN": [
        "Little India Street Food Walking Tour",
        "Banana Leaf Rice Cultural Experience",
        "Spice Route Discovery Walk",
        "South Indian Cooking Masterclass",
        "Tekka Market Food Heritage Tour",
        "Tiffin Carrier Lunch Experience",
        "Curry House Cooking Workshop",
        "Little India Breakfast Immersion",
        "Vegetarian Feast Cultural Journey",
        "Mughlai Biryani Cooking Class",
    ],
    "WESTERN": [
        "Colonial Heritage Dining Experience",
        "Farm-to-Table Culinary Visit",
        "Hotel Heritage Afternoon Tea Tour",
        "Private Chef Garden Dinner",
        "Sunday Brunch Discovery Experience",
        "Craft Brewery Food Pairing Tour",
        "East-Meets-West Fusion Workshop",
        "Dempsey Hill Food & History Walk",
    ],
    "FUSION": [
        "Peranakan Nyonya Cooking Workshop",
        "Traditional Peranakan Culinary Experience",
        "Nonya Heritage Food Trail",
        "Modern Singapore Cuisine Masterclass",
        "Straits Chinese Cooking Class",
        "Baba Nyonya Heritage Dining",
        "East-West Spice Journey",
        "Fusion Hawker Innovation Tour",
        "Katong Peranakan Food Trail",
    ],
    "DESSERT": [
        "Traditional Kueh Making Workshop",
        "Old-School Dessert Discovery Tour",
        "Hawker Dessert Heritage Walk",
        "Nonya Kueh Cultural Experience",
        "Local Sweet Treats Masterclass",
        "Classic Ice Dessert Journey",
        "Confectionery Heritage Workshop",
        "Ondeh Ondeh & Kuih Tasting Trail",
    ],
    "STREET_FOOD": [
        "Hawker Centre Discovery Experience",
        "Singapore Street Food Night Tour",
        "Maxwell Food Centre Heritage Walk",
        "Lau Pa Sat Evening Food Experience",
        "Morning Wet Market Food Tour",
        "HDB Heartland Hawker Journey",
        "Private Kopitiam Culture Experience",
        "Old Airport Road Food Trail",
        "Tiong Bahru Market Discovery Walk",
        "Chinatown Complex Food Experience",
    ],
}

# Cuisine type → static image path mapping
# Paths are relative to STATICFILES_DIRS root (src/static/).
# Templates should resolve these with {% static %}.
IMAGE_MAP = {
    "CHINESE":     "images/experiences/chinatown-tour.png",
    "MALAY":       "images/experiences/kampong-glam.png",
    "INDIAN":      "images/experiences/little-india.png",
    "WESTERN":     "images/experiences/night-market.png",
    "FUSION":      "images/experiences/cooking-class.png",
    "DESSERT":     "images/experiences/kopitiam.png",
    "STREET_FOOD": "images/experiences/hawker-tour.png",
}
# Used when a cuisine type has no dedicated image
_IMAGE_FALLBACK = "images/experiences/peranakan-workshop.png"

# Tourism-focused review snippets
REVIEW_SNIPPETS = [
    "Great cultural immersion and authentic local flavors throughout.",
    "Well-organized tour with a very knowledgeable and friendly guide.",
    "Perfect introduction to Singapore's hawker heritage. Loved every stop.",
    "Highly recommended for first-time visitors wanting the real experience.",
    "Exceeded expectations. Our guide knew every stall owner personally.",
    "A must-do experience. Learned so much about the local food culture.",
    "Beautifully paced experience with generous tastings at each stop.",
    "Our guide was passionate and the history behind each dish was fascinating.",
    "Best tour activity we did during our entire trip to Singapore.",
    "Small group size made it feel personal and very special.",
    "Incredible variety of food stops. Felt well-fed and well-informed.",
    "The behind-the-scenes access to the wet market was a real highlight.",
    "Authentic, educational, and delicious. Ticked every box.",
    "Our guide brought the neighbourhood's history to life beautifully.",
    "Worth every dollar. A genuine insight into local life and food culture.",
    "The cooking workshop component was hands-on and great fun.",
    "Loved the early morning market visit — something tourists rarely see.",
    "Every tasting was expertly chosen to show the full range of flavours.",
    "We came back for a second tour on our next visit. That says it all.",
    "The perfect balance of eating, walking, and cultural storytelling.",
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _rand_lat() -> Decimal:
    """Random latitude within the Singapore bounding box."""
    fraction = Decimal(str(random.random()))
    return (LAT_MIN + (LAT_MAX - LAT_MIN) * fraction).quantize(Decimal("0.000001"))


def _rand_lng() -> Decimal:
    """Random longitude within the Singapore bounding box."""
    fraction = Decimal(str(random.random()))
    return (LNG_MIN + (LNG_MAX - LNG_MIN) * fraction).quantize(Decimal("0.000001"))


def _rand_price() -> Decimal:
    """Experience-based pricing: 85% standard ($45–$180), 15% premium ($200–$350)."""
    if random.random() < 0.15:
        return Decimal(str(random.randint(200, 350)))
    return Decimal(str(random.randint(45, 180)))


def _sg_address() -> str:
    area = random.choice(SG_AREAS)
    postal = random.randint(10000, 829999)
    return f"{random.randint(1, 100)} {area} Road, Singapore {postal:06d}"


# ── Command ──────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Seed the database with tourism food experience data for Singapore."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("\nSeeding database...\n")

        self._clear()
        tourists    = self._create_tourists()
        vendors     = self._create_vendors()
        listings    = self._create_listings(vendors)
        self._create_listing_images(listings)
        bookings    = self._create_bookings(tourists, listings)
        self._create_reviews(tourists, listings)
        itineraries = self._create_itineraries(tourists, listings)
        self._print_summary(tourists, vendors, listings, bookings, itineraries)

    # ── Clear previous seed data ─────────────────────────────────────────────

    def _clear(self):
        deleted, breakdown = CustomUser.objects.filter(
            username__startswith=SEED_PREFIX
        ).delete()
        if deleted:
            details = ", ".join(
                f"{count} {model.split('.')[-1]}"
                for model, count in breakdown.items()
                if count
            )
            self.stdout.write(f"  Cleared {deleted} existing seed record(s) ({details}).")
        else:
            self.stdout.write("  No existing seed data found -- starting fresh.")

    # ── Tourists ─────────────────────────────────────────────────────────────

    def _create_tourists(self) -> list[CustomUser]:
        tourists = []
        for i in range(TOURIST_COUNT):
            user = CustomUser.objects.create_user(
                username=f"{SEED_PREFIX}tourist_{i}",
                email=fake.email(),
                password="seedpass123",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role=CustomUser.Role.TOURIST,
            )
            tourists.append(user)
        self.stdout.write(f"  Created {len(tourists)} tourist user(s).")
        return tourists

    # ── Vendors ──────────────────────────────────────────────────────────────

    def _create_vendors(self) -> list[Vendor]:
        vendors = []
        for i in range(VENDOR_COUNT):
            cuisine = random.choice(CUISINE_VALUES)
            user = CustomUser.objects.create_user(
                username=f"{SEED_PREFIX}vendor_{i}",
                email=fake.email(),
                password="seedpass123",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role=CustomUser.Role.TOURIST,
            )
            # Vendor.save() promotes user.role -> VENDOR when is_approved=True
            vendor = Vendor.objects.create(
                user=user,
                name=f"{fake.last_name()} {random.choice(VENDOR_SUFFIXES)}",
                description=fake.paragraph(nb_sentences=3),
                cuisine_types=cuisine,
                address=_sg_address(),
                latitude=_rand_lat(),
                longitude=_rand_lng(),
                is_approved=True,
            )
            vendors.append(vendor)
        self.stdout.write(f"  Created {len(vendors)} experience operator(s).")
        return vendors

    # ── Listings (experiences) ────────────────────────────────────────────────

    def _create_listings(self, vendors: list[Vendor]) -> list[Listing]:
        bulk = []
        base, extra = divmod(LISTING_COUNT, len(vendors))

        for idx, vendor in enumerate(vendors):
            count = base + (1 if idx < extra else 0)
            for _ in range(count):
                cuisine = random.choice(CUISINE_VALUES)
                name_pool = EXPERIENCE_NAMES.get(cuisine, ["Local Food Experience"])
                bulk.append(Listing(
                    vendor=vendor,
                    title=random.choice(name_pool),
                    description=fake.paragraph(nb_sentences=2),
                    price=_rand_price(),
                    # Experiences: 90–240 minutes, no durations below 60
                    duration=random.choice([90, 120, 150, 180, 210, 240]),
                    max_capacity=random.randint(2, 16),
                    cuisine_type=cuisine,
                    availability=random.choices(
                        [True, False], weights=[9, 1]
                    )[0],
                ))

        Listing.objects.bulk_create(bulk)
        # MySQL's bulk_create doesn't populate PKs on the returned objects,
        # so re-fetch from the DB to get fully-hydrated instances.
        created = list(Listing.objects.filter(vendor__in=vendors).order_by("id"))
        self.stdout.write(f"  Created {len(created)} experience listing(s).")
        return created

    # ── Listing images (cuisine-mapped static paths) ──────────────────────────

    def _create_listing_images(self, listings: list[Listing]) -> None:
        images = [
            ListingImage(
                listing=listing,
                image=IMAGE_MAP.get(listing.cuisine_type, _IMAGE_FALLBACK),
            )
            for listing in listings
        ]
        ListingImage.objects.bulk_create(images)
        self.stdout.write(f"  Created {len(images)} listing image(s) (cuisine-mapped).")

    # ── Bookings ─────────────────────────────────────────────────────────────

    def _create_bookings(
        self, tourists: list[CustomUser], listings: list[Listing]
    ) -> list[Booking]:
        statuses = Booking.Status.values
        bulk = []
        for _ in range(BOOKING_COUNT):
            bulk.append(Booking(
                tourist=random.choice(tourists),
                listing=random.choice(listings),
                booking_date=timezone.make_aware(
                    fake.date_time_between(start_date="-90d", end_date="+45d")
                ),
                party_size=random.randint(1, 8),
                status=random.choice(statuses),
                notes=fake.sentence() if random.random() < 0.4 else "",
            ))
        created = Booking.objects.bulk_create(bulk)
        self.stdout.write(f"  Created {len(created)} booking(s).")
        return created

    # ── Reviews ──────────────────────────────────────────────────────────────

    def _create_reviews(
        self, tourists: list[CustomUser], listings: list[Listing]
    ) -> None:
        # Shuffled pool of unique (tourist, listing) pairs — no duplicates.
        pairs = [
            (tourist, listing)
            for tourist in tourists
            for listing in listings
        ]
        random.shuffle(pairs)

        bulk = [
            Review(
                tourist=tourist,
                listing=listing,
                rating=random.randint(1, 5),
                review_text=random.choice(REVIEW_SNIPPETS),
            )
            for tourist, listing in pairs[:REVIEW_COUNT]
        ]
        Review.objects.bulk_create(bulk)
        self.stdout.write(f"  Created {len(bulk)} tourism review(s).")

    # ── Itineraries ───────────────────────────────────────────────────────────

    def _create_itineraries(
        self, tourists: list[CustomUser], listings: list[Listing]
    ) -> list[Itinerary]:
        itineraries = []
        stops_bulk = []

        for _ in range(ITINERARY_COUNT):
            itin = Itinerary.objects.create(
                tourist=random.choice(tourists),
                title=fake.sentence(nb_words=random.randint(4, 7)).rstrip("."),
                date=fake.date_between(start_date="+1d", end_date="+120d"),
            )
            itineraries.append(itin)

            stop_count = random.randint(2, 5)
            chosen = random.sample(listings, k=min(stop_count, len(listings)))
            for order, listing in enumerate(chosen, start=1):
                stops_bulk.append(ItineraryStop(
                    itinerary=itin,
                    listing=listing,
                    visit_order=order,
                    notes=fake.sentence() if random.random() < 0.5 else "",
                ))

        ItineraryStop.objects.bulk_create(stops_bulk)
        self.stdout.write(
            f"  Created {len(itineraries)} itinerary/itineraries "
            f"with {len(stops_bulk)} stop(s)."
        )
        return itineraries

    # ── Summary ───────────────────────────────────────────────────────────────

    def _print_summary(
        self,
        tourists: list[CustomUser],
        vendors: list[Vendor],
        listings: list[Listing],
        bookings: list[Booking],
        itineraries: list[Itinerary],
    ) -> None:
        bookings_count = Booking.objects.filter(
            tourist__username__startswith=SEED_PREFIX
        ).count()
        reviews_count = Review.objects.filter(
            tourist__username__startswith=SEED_PREFIX
        ).count()
        images_count = ListingImage.objects.filter(
            listing__vendor__user__username__startswith=SEED_PREFIX
        ).count()
        stops_count = ItineraryStop.objects.filter(
            itinerary__tourist__username__startswith=SEED_PREFIX
        ).count()

        # Price stats from in-memory listing objects
        prices = [float(l.price) for l in listings]
        avg_price = sum(prices) / len(prices) if prices else 0
        min_price = min(prices) if prices else 0
        max_price = max(prices) if prices else 0

        # Coordinate range across seeded vendors
        lats = [float(v.latitude) for v in vendors]
        lngs = [float(v.longitude) for v in vendors]
        lat_span_km = (max(lats) - min(lats)) * 111.0
        lng_span_km = (max(lngs) - min(lngs)) * 111.0 * 0.9994  # cos(1.35°)

        self.stdout.write(self.style.SUCCESS(
            "\n-- Seed complete ------------------------------------------"
        ))
        self.stdout.write(f"  Tourist users          : {len(tourists)}")
        self.stdout.write(f"  Experience operators   : {len(vendors)}")
        self.stdout.write(f"  Experience listings    : {len(listings)}")
        self.stdout.write(f"  Listing images         : {images_count}  (cuisine-mapped static)")
        self.stdout.write(f"  Bookings               : {bookings_count}")
        self.stdout.write(f"  Reviews                : {reviews_count}")
        self.stdout.write(f"  Itineraries            : {len(itineraries)}")
        self.stdout.write(f"  Itinerary stops        : {stops_count}")
        self.stdout.write("")
        self.stdout.write(
            f"  Price range            : ${min_price:.0f} to ${max_price:.0f} "
            f"(avg ${avg_price:.0f}) per person"
        )
        self.stdout.write(
            f"  Coordinate spread      : ~{lat_span_km:.1f} km N/S, "
            f"~{lng_span_km:.1f} km E/W  (Singapore bounds)"
        )
        self.stdout.write(self.style.SUCCESS(
            "----------------------------------------------------------\n"
        ))
