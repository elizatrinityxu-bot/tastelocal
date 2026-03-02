from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .decorators import tourist_required
from .forms import TouristRegistrationForm
from .models import CustomUser


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = TouristRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = TouristRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def dashboard(request):
    """Central routing: send each role to its own dashboard."""
    user = request.user
    if user.role == CustomUser.Role.ADMIN:
        return redirect("/admin/")
    if user.role == CustomUser.Role.VENDOR:
        return redirect("vendor_dashboard")
    return redirect("tourist_dashboard")


@tourist_required
def tourist_dashboard(request):
    has_pending_application = hasattr(request.user, "vendor_profile")
    return render(
        request,
        "accounts/tourist_dashboard.html",
        {"user": request.user, "has_pending_application": has_pending_application},
    )
