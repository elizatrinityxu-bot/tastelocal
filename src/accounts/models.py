from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        TOURIST = "TOURIST", "Tourist"
        VENDOR = "VENDOR", "Vendor"
        ADMIN = "ADMIN", "Admin"

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.TOURIST,
    )

    def __str__(self):
        return f"{self.username} ({self.role})"


class UserProfile(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(
        upload_to="profiles/", blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile of {self.user.username}"
