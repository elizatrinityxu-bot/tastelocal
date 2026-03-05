from django.contrib import messages
from django.shortcuts import redirect, render


def about(request):
    return render(request, "pages/about.html")


def how_it_works(request):
    return render(request, "pages/how_it_works.html")


def become_vendor(request):
    return render(request, "pages/become_vendor.html")


def faq(request):
    return render(request, "pages/faq.html")


def contact(request):
    if request.method == "POST":
        messages.success(request, "Thanks for reaching out! We'll be in touch shortly.")
        return redirect("page_contact")
    return render(request, "pages/contact.html")


def terms(request):
    return render(request, "pages/terms.html")


def privacy(request):
    return render(request, "pages/privacy.html")
