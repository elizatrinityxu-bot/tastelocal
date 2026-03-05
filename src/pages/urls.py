from django.urls import path

from . import views

urlpatterns = [
    path("about/",          views.about,         name="page_about"),
    path("how-it-works/",   views.how_it_works,  name="page_how_it_works"),
    path("become-vendor/",  views.become_vendor, name="page_become_vendor"),
    path("faq/",            views.faq,           name="page_faq"),
    path("contact/",        views.contact,       name="page_contact"),
    path("terms/",          views.terms,         name="page_terms"),
    path("privacy/",        views.privacy,       name="page_privacy"),
]
