from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin-dashboard/reviews/", views.admin_reviews, name="admin_reviews"),
    path("admin-dashboard/reviews/<int:pk>/action/", views.admin_review_action, name="admin_review_action"),
    path("admin-dashboard/vendors/", views.admin_vendors, name="admin_vendors"),
    path("admin-dashboard/vendors/<int:pk>/action/", views.admin_vendor_action, name="admin_vendor_action"),
]
