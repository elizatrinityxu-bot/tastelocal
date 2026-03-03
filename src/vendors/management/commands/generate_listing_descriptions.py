"""
Management command: generate_listing_descriptions
Usage: python manage.py generate_listing_descriptions [--dry-run]

Generates structured, professional descriptions for every Listing.
Each description contains four sections:

  1. Overview        — one-paragraph narrative introduction
  2. What to Expect  — 4 bullet highlights tailored to the experience type
  3. Experience Details — duration, host, and group size
  4. Perfect For     — target audience sentence

Experience type is inferred from keywords in the listing title.
Fields modified : description only.
Fields untouched: price, duration, availability, and all other fields.
"""

import random

from django.core.management.base import BaseCommand

from vendors.models import CuisineType, Listing

# ── Experience-type inference ─────────────────────────────────────────────────
#
# Checked in order — most specific phrases first so "Cooking Class" is matched
# before the generic "tour" fallback.

_EXPERIENCE_RULES: list[tuple[str, list[str]]] = [
    ("cooking_class", ["cooking class", "cook class", "cooking masterclass",
                       "masterclass", "cook masterclass"]),
    ("workshop",      ["workshop", "spice blending", "kueh making",
                       "kuih making", "rempah", "confectionery"]),
    ("market_tour",   ["wet market", "market tour", "market food", "tekka market",
                       "maxwell food", "lau pa sat"]),
    ("food_trail",    ["food trail", "street food", "hawker trail",
                       "nonya trail", "heritage trail"]),
    ("walking_tour",  ["walking tour", "heritage walk", "food walk",
                       "culture walk", "cultural walk", "hawker walk"]),
    ("guided_tour",   ["food tour", "gastro tour", "culinary tour",
                       "hawker tour", "night tour", "tour"]),
    ("feast",         ["feast", "dining experience", "dinner", "supper",
                       "breakfast", "brunch", "tiffin", "biryani"]),
    ("immersive",     ["experience", "journey", "immersion", "discovery",
                       "cultural", "heritage", "culture"]),
]

_FALLBACK_TYPE = "guided_tour"


def _infer_experience_type(title: str) -> str:
    lower = title.lower()
    for exp_type, keywords in _EXPERIENCE_RULES:
        if any(kw in lower for kw in keywords):
            return exp_type
    return _FALLBACK_TYPE


# ── Cuisine context phrases ───────────────────────────────────────────────────

_CUISINE_CONTEXT: dict[str, str] = {
    "CHINESE":     "Singapore's Chinese culinary heritage",
    "MALAY":       "Malay culinary traditions and kampong culture",
    "INDIAN":      "South and North Indian spice culture",
    "WESTERN":     "colonial and modern Western dining in Singapore",
    "FUSION":      "Peranakan and Straits Chinese fusion cuisine",
    "DESSERT":     "traditional Singapore desserts and heritage sweet treats",
    "STREET_FOOD": "Singapore's iconic hawker street food culture",
}

_CUISINE_LABEL_MAP: dict[str, str] = dict(CuisineType.choices)


# ── Section 1 — Overview paragraphs ──────────────────────────────────────────
#
# Two variants per type. Placeholders: {vendor}, {cuisine_label},
# {cuisine_context}, {duration}.

_OVERVIEWS: dict[str, list[str]] = {

    "cooking_class": [
        (
            "Join {vendor} for this hands-on {cuisine_label} cooking class — one of Singapore's "
            "most rewarding culinary experiences. Over {duration} minutes, an expert local host "
            "guides you through authentic techniques and time-honoured recipes rooted in "
            "{cuisine_context}. You will prepare traditional dishes from scratch, discover the "
            "stories behind each ingredient, and leave with the skills and recipes to recreate "
            "these flavours at home."
        ),
        (
            "Step into the kitchen with {vendor} and unlock the art of {cuisine_label} cooking. "
            "Designed for curious food lovers, this immersive {duration}-minute class goes beyond "
            "tasting — you will understand the craft, sourcing, and cultural significance behind "
            "each dish. Your passionate host draws on a deep knowledge of {cuisine_context} to "
            "make every lesson both delicious and genuinely memorable."
        ),
    ],

    "workshop": [
        (
            "This hands-on workshop hosted by {vendor} offers an intimate introduction to "
            "{cuisine_context}. Across {duration} minutes, you will be guided through traditional "
            "artisan processes and techniques that have shaped Singapore's food culture for "
            "generations. Small group sizes ensure every participant receives personalised "
            "attention and leaves with a real, practised skill."
        ),
        (
            "Hosted by {vendor}, this {duration}-minute workshop is an unmissable opportunity to "
            "engage with {cuisine_context} at a depth most visitors never experience. Working "
            "hands-on with authentic ingredients under the guidance of a passionate local expert, "
            "you will master techniques passed down through families and communities across "
            "Singapore's rich culinary history."
        ),
    ],

    "market_tour": [
        (
            "Start your morning the local way with {vendor} on this immersive market tour rooted "
            "in {cuisine_context}. Over {duration} minutes, your knowledgeable guide navigates "
            "the vibrant stalls of a traditional Singapore market — identifying fresh produce, "
            "explaining seasonal ingredients, and revealing the supply chain behind the city's "
            "beloved hawker dishes. An eye-opening experience for every serious food lover."
        ),
        (
            "This {duration}-minute market experience with {vendor} offers a rare behind-the-scenes "
            "look at the foundations of {cuisine_context}. Walk through bustling wet market "
            "corridors, meet familiar traders, and learn the daily rituals that keep Singapore's "
            "food culture honest, fresh, and deeply rooted in community."
        ),
    ],

    "food_trail": [
        (
            "Explore Singapore's most vibrant flavours on this curated food trail hosted by "
            "{vendor}. Over {duration} minutes, your guide leads you through hidden gems and "
            "legendary stalls that define {cuisine_context} — each stop chosen to showcase the "
            "depth and diversity of local food culture, from humble hawker classics to "
            "neighbourhood institutions that have stood for decades."
        ),
        (
            "Join {vendor} on a guided food trail through Singapore's most storied culinary "
            "neighbourhoods. This {duration}-minute journey celebrates {cuisine_context}, weaving "
            "together authentic tastings, cultural history, and personal stories from the people "
            "behind each dish. Designed for travellers who believe the best way to know a city "
            "is through its food."
        ),
    ],

    "walking_tour": [
        (
            "Walk the streets of Singapore with {vendor} on this food-focused heritage tour. "
            "In {duration} minutes, your local guide reveals the history, communities, and "
            "dishes that make {cuisine_context} one of the city's most treasured legacies. "
            "Expect authentic tastings, insider knowledge, and a genuine connection to the "
            "neighbourhoods that have kept these traditions alive across generations."
        ),
        (
            "This {duration}-minute walking tour, led by {vendor}, invites you to discover "
            "{cuisine_context} through the eyes of a passionate local. Navigate lively markets, "
            "heritage streets, and beloved eateries, pausing for thoughtfully curated tastings "
            "that tell the story of Singapore one bite at a time. Comfortable walking pace "
            "suitable for all fitness levels."
        ),
    ],

    "guided_tour": [
        (
            "Hosted by {vendor}, this guided culinary tour is your passport to the authentic "
            "world of {cuisine_context}. Across {duration} minutes, you will visit iconic "
            "locations, meet the artisans and hawkers who keep these traditions alive, and enjoy "
            "a series of curated tastings that capture the true spirit of Singapore's food "
            "heritage. Ideal for first-time visitors and returning enthusiasts alike."
        ),
        (
            "Experience Singapore's culinary landscape through the expertise of {vendor}. "
            "This {duration}-minute guided tour focuses on {cuisine_context}, taking you beyond "
            "tourist menus to the real flavours locals cherish. Your guide brings each "
            "neighbourhood to life with historical anecdotes, cultural context, and "
            "unforgettable food discoveries at every turn."
        ),
    ],

    "feast": [
        (
            "Gather around the table with {vendor} for a convivial celebration of "
            "{cuisine_context}. This {duration}-minute experience centres on the joy of sharing — "
            "generous servings, warm hospitality, and the kind of honest, flavour-packed food "
            "that Singaporeans have treasured for generations. A perfect choice for groups "
            "seeking genuine local connection over a memorable meal."
        ),
        (
            "Join {vendor} for a {duration}-minute dining experience that honours the very best "
            "of {cuisine_context}. Each dish is prepared with care and served with the stories "
            "that give it meaning — creating a meal that is as culturally enriching as it is "
            "delicious. Ideal for travellers who want to eat well and leave knowing a little "
            "more about Singapore's culinary soul."
        ),
    ],

    "immersive": [
        (
            "Crafted by {vendor}, this {duration}-minute experience offers an authentic immersion "
            "into {cuisine_context}. Whether you are a first-time visitor or a returning food "
            "enthusiast, you will come away with a deeper appreciation of Singapore's diverse "
            "culinary identity and the passionate communities who preserve it for future "
            "generations."
        ),
        (
            "This signature experience from {vendor} celebrates the richness of {cuisine_context} "
            "through a thoughtfully curated {duration}-minute programme. Combining authentic "
            "tastings, cultural storytelling, and hands-on moments, it offers a genuine window "
            "into the food traditions that make Singapore one of Asia's most beloved culinary "
            "destinations."
        ),
    ],
}


# ── Section 2 — Highlights pools ─────────────────────────────────────────────
#
# 6 candidates per type — 4 are randomly sampled per listing, ensuring variety
# even when multiple listings share the same experience type.
# Placeholders: {cuisine_context}, {cuisine_label}.

_HIGHLIGHTS: dict[str, list[str]] = {

    "cooking_class": [
        "Hands-on preparation of traditional {cuisine_label} dishes guided by a local expert",
        "Authentic techniques and family recipes rooted in {cuisine_context}",
        "Learn to select, prepare, and plate ingredients the way locals do",
        "Take home printed recipes to recreate every dish in your own kitchen",
        "Understand the cultural stories and history behind each recipe",
        "Personalised instruction throughout — suitable for all experience levels",
    ],

    "workshop": [
        "Artisan skills practised under expert guidance in an intimate setting",
        "Work with authentic, locally sourced ingredients from start to finish",
        "Discover the heritage and cultural stories behind each traditional technique",
        "Leave with a tangible result you have crafted with your own hands",
        "Limited group sizes for a personalised and focused learning experience",
        "Deep engagement with {cuisine_context} craftsmanship rarely found in guided tours",
    ],

    "market_tour": [
        "Navigate bustling wet market stalls with a knowledgeable local guide",
        "Identify seasonal produce and learn to select the freshest ingredients",
        "Meet the traders and hawker suppliers who keep Singapore's kitchens alive",
        "Understand the daily supply chain that underpins {cuisine_context}",
        "Sample fresh produce and snacks as you explore each section of the market",
        "Gain insider knowledge of how Singaporeans source and prepare food at home",
    ],

    "food_trail": [
        "Curated stops at legendary local stalls and off-the-radar neighbourhood gems",
        "Authentic tastings at every stop, guided by an expert in {cuisine_context}",
        "Cultural history and community storytelling woven into every part of the journey",
        "Discover the families and hawkers who have kept these dishes alive for generations",
        "Routes designed to take you beyond the tourist trail and into real local life",
        "A balanced mix of eating, walking, and cultural discovery throughout",
    ],

    "walking_tour": [
        "Guided walk through heritage streets and vibrant local neighbourhoods",
        "Curated tastings at stalls and eateries selected for authenticity and flavour",
        "In-depth historical and cultural commentary at every key stop",
        "Intimate group format for a personal, unhurried pace throughout",
        "Cover more culinary ground than any self-guided exploration could achieve",
        "Photogenic stops at Singapore's most characterful food landmarks",
    ],

    "guided_tour": [
        "Expert local guide with deep, first-hand knowledge of {cuisine_context}",
        "Access to insider stalls and iconic locations not found in any guidebook",
        "Curated tasting programme showcasing the full range of local flavours",
        "Cultural storytelling that brings each neighbourhood and dish to life",
        "Thoughtfully paced itinerary suited to curious, engaged food travellers",
        "All logistics managed by your host so you can focus entirely on the experience",
    ],

    "feast": [
        "Generous servings of traditional dishes prepared fresh for your group",
        "Warm, communal dining environment rooted in genuine local hospitality",
        "Cultural introduction to every dish — its origins, ingredients, and significance",
        "Ingredients sourced from trusted local suppliers committed to authenticity",
        "A shared table format that encourages conversation and connection",
        "Contextual stories and food history provided throughout the meal",
    ],

    "immersive": [
        "A deeply curated programme blending food, culture, and authentic community access",
        "Led by passionate local hosts with genuine expertise in {cuisine_context}",
        "Thoughtful balance of tasting, learning, and hands-on cultural exploration",
        "Genuine insight into the heritage traditions that shape Singapore's culinary identity",
        "Small group format ensuring a personal, meaningful, and unhurried experience",
        "Suitable for all backgrounds — no prior culinary knowledge required",
    ],
}


# ── Section 4 — Perfect For ───────────────────────────────────────────────────
#
# Two variants per type for additional variation.

_PERFECT_FOR: dict[str, list[str]] = {

    "cooking_class": [
        "Food lovers, home cooks, and curious travellers seeking a hands-on connection with "
        "Singapore's culinary traditions. Suitable for all experience levels.",
        "Anyone who wants to go beyond eating and truly understand the craft behind Singapore's "
        "most beloved dishes — no cooking experience required.",
    ],

    "workshop": [
        "Craft enthusiasts, cultural explorers, and travellers who prefer learning by doing "
        "over passive sightseeing.",
        "Visitors who want a meaningful souvenir — not something bought, but something made "
        "with their own hands under expert local guidance.",
    ],

    "market_tour": [
        "Early risers, aspiring cooks, food photographers, and anyone who wants to understand "
        "Singapore's legendary hawker culture from the ground up.",
        "Travellers who are as interested in how food is grown and sourced as in how it tastes "
        "— a perfect complement to any broader food tour.",
    ],

    "food_trail": [
        "First-time visitors and returning travellers who want to eat authentically, explore "
        "local neighbourhoods, and discover Singapore's food identity beyond the tourist trail.",
        "Groups of two to four who enjoy walking, eating, and listening to the stories behind "
        "the food they love — the ideal half-day experience in Singapore.",
    ],

    "walking_tour": [
        "Curious travellers, history enthusiasts, and food lovers who enjoy combining cultural "
        "discovery with authentic local eating at a comfortable, enjoyable pace.",
        "Anyone visiting Singapore for the first time who wants to understand the city's "
        "heritage through its most honest and beloved tradition — its food.",
    ],

    "guided_tour": [
        "Travellers of all backgrounds looking for a structured, expert-led introduction to "
        "Singapore's rich and diverse food culture.",
        "Visitors who want a memorable, organised culinary experience without the effort of "
        "planning — just turn up and let your guide do the rest.",
    ],

    "feast": [
        "Groups, families, and couples seeking a convivial, flavour-packed meal rooted in "
        "genuine local tradition and warm Singaporean hospitality.",
        "Travellers celebrating a special occasion, or anyone who simply wants to sit down, "
        "relax, and eat extremely well in good company.",
    ],

    "immersive": [
        "Travellers who go beyond the surface — those who want to understand, connect with, "
        "and genuinely experience Singapore's food culture rather than simply observe it.",
        "Open-minded explorers who value depth over speed and believe the best travel memories "
        "are made around a shared table with a knowledgeable local host.",
    ],
}


# ── Builder ───────────────────────────────────────────────────────────────────
#
# Produces HTML stored directly in the description TextField.
# Rendered in the template with {{ listing.description|safe }}.

def _build_description(listing: Listing) -> str:
    exp_type = _infer_experience_type(listing.title)

    ctx = dict(
        vendor=listing.vendor.name,
        cuisine_label=_CUISINE_LABEL_MAP.get(listing.cuisine_type, listing.cuisine_type),
        cuisine_context=_CUISINE_CONTEXT.get(
            listing.cuisine_type, "Singapore's culinary heritage"
        ),
        duration=listing.duration,
    )

    # Section 1 — Overview
    overview = random.choice(
        _OVERVIEWS.get(exp_type, _OVERVIEWS[_FALLBACK_TYPE])
    ).format(**ctx)

    # Section 2 — Highlights (4 randomly sampled from pool of 6)
    highlight_pool = _HIGHLIGHTS.get(exp_type, _HIGHLIGHTS[_FALLBACK_TYPE])
    highlight_items = "".join(
        f"<li>{h.format(**ctx)}</li>"
        for h in random.sample(highlight_pool, k=min(4, len(highlight_pool)))
    )

    # Section 3 — Experience Details
    detail_items = (
        f"<li>Duration: {listing.duration} minutes</li>"
        f"<li>Hosted by: {listing.vendor.name}</li>"
        f"<li>Group size: Up to {listing.max_capacity} guests</li>"
    )

    # Section 4 — Perfect For
    perfect_for = random.choice(
        _PERFECT_FOR.get(exp_type, _PERFECT_FOR[_FALLBACK_TYPE])
    )

    return (
        f"<p>{overview}</p>"
        f"<p><strong>What to Expect</strong></p>"
        f"<ul>{highlight_items}</ul>"
        f"<p><strong>Experience Details</strong></p>"
        f"<ul>{detail_items}</ul>"
        f"<p><strong>Perfect For</strong></p>"
        f"<p>{perfect_for}</p>"
    )


# ── Command ───────────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = (
        "Generate structured, tourism-focused descriptions for all Listing objects. "
        "Only the description field is modified."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview generated descriptions without writing to the database.",
        )

    def handle(self, *args, **options):
        dry_run: bool = options["dry_run"]

        listings: list[Listing] = list(
            Listing.objects.select_related("vendor").order_by("cuisine_type", "title")
        )

        if not listings:
            self.stdout.write("No listings found — nothing to update.")
            return

        self.stdout.write(
            f"\nGenerating descriptions for {len(listings)} listing(s)"
            f"{' (dry run — no changes saved)' if dry_run else ''}...\n"
        )

        for listing in listings:
            listing.description = _build_description(listing)

            if dry_run:
                self.stdout.write(
                    f"-- [{listing.get_cuisine_type_display()}] {listing.title} --\n"
                    f"{listing.description}\n"
                )

        if not dry_run:
            Listing.objects.bulk_update(listings, ["description"])
            self.stdout.write(
                self.style.SUCCESS(
                    f"Updated description for {len(listings)} listing(s)."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"Dry run complete — {len(listings)} description(s) previewed, "
                    "none saved."
                )
            )
