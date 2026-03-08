from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied


def tourist_or_vendor_required(view_func):
    """Allow both TOURIST and approved VENDOR users; block staff/admin."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if request.user.is_staff or request.user.role == "ADMIN":
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped


def tourist_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if request.user.role != "TOURIST":
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped


def vendor_required(view_func):
    """
    Requires role=VENDOR AND is_approved=True on the linked Vendor record.
    """

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        user = request.user
        if user.role != "VENDOR":
            raise PermissionDenied
        try:
            if not user.vendor_profile.is_approved:
                raise PermissionDenied
        except ObjectDoesNotExist:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())
        if request.user.role != "ADMIN":
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return _wrapped
