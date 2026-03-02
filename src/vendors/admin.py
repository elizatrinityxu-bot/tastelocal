from django.contrib import admin

from .models import Listing, ListingImage, Vendor


def approve_vendors(modeladmin, request, queryset):
    """
    Admin action: approve selected vendors and set their user role to VENDOR.
    Both steps must happen together for the vendor dashboard to become accessible.
    """
    for vendor in queryset.select_related("user"):
        vendor.is_approved = True
        vendor.save(update_fields=["is_approved"])
        vendor.user.role = "VENDOR"
        vendor.user.save(update_fields=["role"])


approve_vendors.short_description = "Approve selected vendors"


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "is_approved", "created_at")
    list_filter = ("is_approved",)
    search_fields = ("name", "user__username")
    actions = [approve_vendors]


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "vendor", "price", "duration", "availability")
    list_filter = ("availability", "cuisine_type")
    search_fields = ("title", "vendor__name")
    inlines = [ListingImageInline]


@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    list_display = ("listing", "created_at")
