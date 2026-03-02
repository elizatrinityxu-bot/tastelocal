from django.contrib import admin

from .models import Review, ReviewResponse


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("listing", "tourist", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("tourist__username", "listing__title")


@admin.register(ReviewResponse)
class ReviewResponseAdmin(admin.ModelAdmin):
    list_display = ("review", "vendor", "created_at")
    search_fields = ("vendor__username",)
