from django.conf import settings
from django.db import models


class CuisineType(models.TextChoices):
    CHINESE = "CHINESE", "Chinese"
    MALAY = "MALAY", "Malay"
    INDIAN = "INDIAN", "Indian"
    WESTERN = "WESTERN", "Western"
    FUSION = "FUSION", "Fusion"
    DESSERT = "DESSERT", "Dessert"
    STREET_FOOD = "STREET_FOOD", "Street Food"


class Vendor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vendor_profile",
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    cuisine_types = models.CharField(
        max_length=20,
        choices=CuisineType.choices,
    )
    address = models.CharField(max_length=500)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Keep user.role in sync: whenever is_approved becomes True,
        # promote the linked user to VENDOR automatically.
        # This fires for admin form saves, bulk actions, and any other path.
        if self.is_approved:
            from django.contrib.auth import get_user_model
            get_user_model().objects.filter(pk=self.user_id).update(role="VENDOR")

    def __str__(self):
        return self.name


class Listing(models.Model):
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name="listings",
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.PositiveIntegerField(help_text="Duration in minutes")
    max_capacity = models.PositiveIntegerField()
    cuisine_type = models.CharField(
        max_length=20,
        choices=CuisineType.choices,
    )
    availability = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class ListingImage(models.Model):
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(upload_to="listings/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.listing.title}"
