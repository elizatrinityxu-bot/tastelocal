from django.urls import path

from . import views

urlpatterns = [
    path("dashboard/", views.vendor_dashboard, name="vendor_dashboard"),
    path("apply/", views.apply_vendor, name="apply_vendor"),
    path("pending/", views.pending_vendor, name="pending_vendor"),
]
