"""
Management command: seed_data
Usage: python manage.py seed_data

Populates the database with realistic tourism food experience data.
Existing seed data (identified by the 'seed_' username prefix) is
cleared before new records are inserted.  All writes are wrapped in
a single transaction — an error rolls everything back cleanly.
"""

import random
from datetime import datetime, time
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
LISTING_COUNT = 38
BOOKING_COUNT = 60
REVIEW_COUNT = 100
ITINERARY_COUNT = 10

# Approved booking time slots — vendor operating hours 09:00–21:00
BOOKING_TIME_SLOTS = [
    time(9, 0), time(9, 30), time(10, 0), time(10, 30),
    time(11, 30), time(12, 0), time(12, 30), time(13, 0),
    time(14, 0), time(14, 30), time(15, 0), time(15, 30),
    time(18, 0), time(18, 30), time(19, 0), time(19, 30),
    time(20, 0), time(20, 30),
]

ITINERARY_NAMES = [
    "Singapore Hawker Adventure",
    "Little India Food Trail",
    "Chinatown Street Food Walk",
    "Kampong Glam Culinary Journey",
    "Katong Heritage Food Tour",
    "One Day Singapore Food Explorer",
    "Geylang Night Market Trail",
    "Tiong Bahru Cafe & Hawker Hop",
    "East Coast Seafood Journey",
    "Joo Chiat Peranakan Food Walk",
]

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

# One listing per image — (image, title, cuisine, description).
# Descriptions are tourist-friendly single sentences (15–25 words).
_IMG = "images/experiences/"
LISTINGS = [
    # CHINESE
    (_IMG + "chinatown-food-walk.png",             "Chinatown Food Walk",                       "CHINESE",
     "Stroll through Chinatown's historic lanes sampling hawker favourites and discovering Singapore's rich Chinese food heritage."),
    (_IMG + "chinatown-street-food-walk.png",      "Chinatown Street Food Walk",                "CHINESE",
     "Explore Chinatown's famous street food stalls and taste iconic dishes while learning about the area's vibrant culinary history."),
    (_IMG + "chinatown-tour.png",                  "Chinatown Heritage Tour",                   "CHINESE",
     "Discover Chinatown's storied past through its heritage shophouses, traditional kopitiams, and beloved local flavours."),
    (_IMG + "heritage-food-street-singapore.png",  "Singapore Heritage Food Street Walk",       "CHINESE",
     "Walk Singapore's most celebrated heritage food streets and savour classic dishes passed down through generations."),
    (_IMG + "kopitiam-breakfast-table.png",        "Traditional Kopitiam Breakfast Experience", "CHINESE",
     "Start the day the Singaporean way with kaya toast, soft-boiled eggs, and freshly brewed kopi at a classic kopitiam."),
    (_IMG + "kopitiam-food-experience.png",        "Kopitiam Food Culture Experience",          "CHINESE",
     "Immerse yourself in Singapore's beloved kopitiam culture, sampling traditional breakfast staples and learning about their Hainanese roots."),
    (_IMG + "kopitiam.png",                        "Classic Kopitiam Culture Tour",             "CHINESE",
     "Step inside a traditional Singaporean kopitiam and enjoy a guided tasting of heritage coffee, toast, and local breakfast favourites."),
    (_IMG + "wet-market-morning-tour.png",         "Morning Wet Market Food Tour",              "CHINESE",
     "Explore a bustling Singapore wet market at dawn, uncovering fresh produce, local ingredients, and the stories behind them."),
    (_IMG + "wet-market-tour.png",                 "Wet Market Heritage Tour",                  "CHINESE",
     "Discover the vibrant rhythm of a traditional wet market and learn how fresh ingredients shape Singapore's iconic everyday cuisine."),
    # MALAY
    (_IMG + "kampong-glam-food-tour.png",          "Kampong Glam Food Tour",                    "MALAY",
     "Tour the historic Kampong Glam neighbourhood and sample rich Malay and Middle Eastern flavours in this culturally vibrant district."),
    (_IMG + "kampong-glam-golden-hour-tour.png",   "Kampong Glam Golden Hour Tour",             "MALAY",
     "Experience Kampong Glam's stunning architecture and aromatic Malay street food as the district glows in the evening light."),
    (_IMG + "kampong-glam.png",                    "Kampong Glam Cultural Experience",          "MALAY",
     "Explore Kampong Glam's rich Malay heritage through its mosques, colourful shopfronts, and authentic traditional cuisine."),
    (_IMG + "satay-grill-night-market.png",        "Satay Grill Night Market Experience",       "MALAY",
     "Gather around a charcoal satay grill at a lively night market and enjoy smoky skewers paired with peanut sauce and ketupat."),
    (_IMG + "satay-street-food-night.png",         "Satay Street Food Night Tour",              "MALAY",
     "Join a night tour through Singapore's most iconic satay spots and savour perfectly grilled skewers under the evening sky."),
    # INDIAN
    (_IMG + "little-india-food-walk.png",          "Little India Street Food Walk",             "INDIAN",
     "Wander through Little India's colourful streets and taste vibrant South Indian street food, spices, and freshly made snacks."),
    (_IMG + "little-india-spice-market-tour.png",  "Little India Spice Market Tour",            "INDIAN",
     "Explore Little India's aromatic spice markets and discover the bold flavours and rich traditions behind Indian cuisine in Singapore."),
    (_IMG + "little-india.png",                    "Little India Cultural Food Experience",     "INDIAN",
     "Discover Little India's culinary soul through a guided tasting of banana leaf rice, roti prata, and freshly brewed teh tarik."),
    (_IMG + "singapore-spice-market.png",          "Singapore Spice Market Discovery",          "INDIAN",
     "Dive into Singapore's spice trading heritage and learn how aromatic ingredients from across Asia shaped the city's diverse cuisine."),
    # WESTERN
    (_IMG + "marina-bay-food-walk.png",            "Marina Bay Food & Heritage Walk",           "WESTERN",
     "Stroll along the iconic Marina Bay waterfront, uncovering Singapore's colonial dining heritage and modern culinary landmarks."),
    # FUSION
    (_IMG + "cooking-class.png",                   "Singapore Cooking Class Experience",        "FUSION",
     "Join a hands-on cooking class and learn to prepare classic Singaporean dishes guided by an experienced local chef."),
    (_IMG + "peranakan-dessert-tasting.png",       "Peranakan Dessert Tasting Experience",      "FUSION",
     "Discover the intricate art of Peranakan dessert-making through a curated tasting of traditional kuih and Nyonya sweet treats."),
    (_IMG + "peranakan-workshop.png",              "Peranakan Nyonya Cooking Workshop",         "FUSION",
     "Learn to prepare authentic Nyonya recipes in this immersive workshop celebrating the unique Peranakan culinary heritage of Singapore."),
    (_IMG + "singapore-cooking-class-group.png",   "Singapore Group Cooking Class",             "FUSION",
     "Cook alongside fellow food lovers in a lively group session, mastering classic Singaporean recipes under expert local guidance."),
    (_IMG + "singapore-cooking-class.png",         "Singapore Culinary Cooking Class",          "FUSION",
     "Sharpen your culinary skills with a focused cooking class covering Singapore's most beloved dishes and traditional cooking techniques."),
    # DESSERT
    (_IMG + "heritage-dessert-tasting.png",        "Heritage Dessert Tasting Experience",       "DESSERT",
     "Sample a curated selection of time-honoured Singaporean desserts and discover the stories and cultural roots behind each sweet treat."),
    (_IMG + "singapore-kuih-dessert-display.png",  "Traditional Kuih & Dessert Showcase",       "DESSERT",
     "Discover traditional Singaporean kuih and heritage desserts while learning about their cultural significance and artisan craftsmanship."),
    # STREET_FOOD
    (_IMG + "hawker-centre-lunch-tour.png",        "Hawker Centre Lunch Tour",                  "STREET_FOOD",
     "Join a guided lunch tour of a bustling hawker centre and sample an exciting variety of Singapore's most beloved street dishes."),
    (_IMG + "hawker-centre-tour.png",              "Hawker Centre Discovery Tour",              "STREET_FOOD",
     "Explore one of Singapore's iconic hawker centres and let a local guide introduce you to the must-try dishes and hidden gems."),
    (_IMG + "hawker-centre-wide-view.png",         "Maxwell Hawker Centre Food Experience",     "STREET_FOOD",
     "Experience Maxwell Food Centre's legendary dishes, from the famous chicken rice to traditional desserts and fragrant laksa."),
    (_IMG + "hawker-chef-cooking.png",             "Hawker Chef Cooking Masterclass",           "STREET_FOOD",
     "Watch a seasoned hawker chef at work and learn the techniques behind Singapore's most iconic wok-fried and grilled street dishes."),
    (_IMG + "hawker-cooking-demo.png",             "Hawker Cooking Demonstration",              "STREET_FOOD",
     "Witness the skill and speed of a hawker cook in action as they demonstrate the preparation of Singapore's favourite local dishes."),
    (_IMG + "hawker-food-table-spread.png",        "Hawker Feast Table Experience",             "STREET_FOOD",
     "Sit down to a generous hawker feast and taste a wide spread of Singapore's best street food all in one memorable sitting."),
    (_IMG + "hawker-tour.png",                     "Singapore Hawker Heritage Tour",            "STREET_FOOD",
     "Trace Singapore's world-famous hawker heritage through a guided tour of historic centres, local favourites, and iconic stall stories."),
    (_IMG + "lau-pa-sat-night-food.png",           "Lau Pa Sat Night Food Experience",          "STREET_FOOD",
     "Spend an unforgettable evening at Lau Pa Sat savouring sizzling satay, fragrant noodles, and the vibrant hawker atmosphere."),
    (_IMG + "lau-pa-sat-satay-night.png",          "Lau Pa Sat Satay Night Tour",               "STREET_FOOD",
     "Join a satay-focused night tour at the iconic Lau Pa Sat market and enjoy perfectly charred skewers fresh off the grill."),
    (_IMG + "night-market.png",                    "Singapore Night Market Food Tour",          "STREET_FOOD",
     "Explore Singapore's lively night market scene and taste an exciting range of street food, snacks, and local delicacies after dark."),
    (_IMG + "singapore-food-guide-explaining.png", "Guided Singapore Food Discovery Tour",      "STREET_FOOD",
     "Follow an expert local guide on a curated food discovery tour across Singapore's most authentic and flavour-packed hawker spots."),
    (_IMG + "street-food-stall-singapore.png",     "Singapore Street Food Stall Experience",    "STREET_FOOD",
     "Experience Singapore's vibrant hawker culture and sample iconic dishes from local street food vendors at a traditional stall."),
]

# Tourism-focused review snippets
BOOKING_NOTES = [
    "Vegetarian preference",
    "Birthday celebration",
    "Food allergy: peanuts",
    "Food allergy: shellfish",
    "Gluten-free required",
    "Halal food only",
    "Vegan preference",
    "Anniversary dinner",
    "Corporate group outing",
    "First visit to Singapore",
]

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
    """Experience-based pricing: $60–$180 per person."""
    return Decimal(str(random.randint(60, 180)))


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
        # Shuffle LISTINGS so cuisine types are spread across vendors randomly.
        pool = list(LISTINGS)
        random.shuffle(pool)

        # Distribute evenly across vendors (38 listings / 10 vendors).
        base, extra = divmod(len(pool), len(vendors))
        bulk = []
        pool_iter = iter(pool)

        for idx, vendor in enumerate(vendors):
            count = base + (1 if idx < extra else 0)
            for _, title, cuisine, description in [next(pool_iter) for _ in range(count)]:
                bulk.append(Listing(
                    vendor=vendor,
                    title=title,
                    description=description,
                    price=_rand_price(),
                    duration=random.choice([90, 120, 150, 180, 210]),
                    max_capacity=random.randint(2, 8),
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

    # ── Listing images (one unique image per listing, derived from LISTINGS) ─────

    def _create_listing_images(self, listings: list[Listing]) -> None:
        # Build title → image path lookup directly from LISTINGS — no random fallback needed.
        title_to_image = {title: image for image, title, *_ in LISTINGS}
        images = [
            ListingImage(
                listing=listing,
                image=title_to_image[listing.title],
            )
            for listing in listings
        ]
        ListingImage.objects.bulk_create(images)
        self.stdout.write(f"  Created {len(images)} listing image(s) (one unique image per listing).")

    # ── Bookings ─────────────────────────────────────────────────────────────

    def _create_bookings(
        self, tourists: list[CustomUser], listings: list[Listing]
    ) -> list[Booking]:
        # EXPIRED and CANCELLED_BY_TOURIST are derived states — never seed directly.
        statuses = [
            Booking.Status.PENDING,
            Booking.Status.CONFIRMED,
            Booking.Status.CANCELLED,
            Booking.Status.COMPLETED,
        ]
        bulk = []
        for _ in range(BOOKING_COUNT):
            bulk.append(Booking(
                tourist=random.choice(tourists),
                listing=random.choice(listings),
                booking_date=timezone.make_aware(
                    datetime.combine(
                        fake.date_between(start_date="-90d", end_date="+45d"),
                        random.choice(BOOKING_TIME_SLOTS),
                    )
                ),
                party_size=random.randint(1, 8),
                status=random.choice(statuses),
                notes=random.choice(BOOKING_NOTES) if random.random() < 0.4 else "",
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
                rating=random.randint(3, 5),
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
                title=random.choice(ITINERARY_NAMES),
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
                    notes=random.choice(BOOKING_NOTES) if random.random() < 0.3 else "",
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
