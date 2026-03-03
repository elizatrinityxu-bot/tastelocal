• CustomUser: Extends Django's AbstractUser. Has a 'role' field (TOURIST / VENDOR / ADMIN). One-to-one with UserProfile.
•	Vendor: Linked to a CustomUser with role=VENDOR. Has a name, description, cuisine types, address, latitude, longitude, and approval status.
•	Listing: A specific food experience offered by a Vendor. Has title, description, price, duration, max_capacity, cuisine_type, and availability.
•	ListingImage: One-to-many with Listing. Stores image file references for vendor gallery photos.
•	Booking: Created by a Tourist (CustomUser). References a Listing. Has booking_date, party_size, status (PENDING / CONFIRMED / CANCELLED / COMPLETED), and notes.
•	Review: Created by a Tourist. References a Listing. Has rating (1–5), review_text, and created_at.
•	ReviewResponse: One-to-one with Review. Created by Vendor to respond to a tourist review.
•	Itinerary: Created by a Tourist. Has a title and date. Contains many ItineraryStop records.
•	ItineraryStop: Many-to-one with Itinerary. References a Listing. Has visit_order and notes.
