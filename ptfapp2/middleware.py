from django.shortcuts import redirect
from django.urls import reverse
    
class RememberMeMiddleware:
    
    """
    Sets session expiry based on remember_me checkbox on login POST.
    Registered in settings.py MIDDLEWARE list.

    ✅ FIXED: old version set expiry BEFORE Django's auth middleware ran,
       so session wasn't actually saved with the correct expiry.
       Now uses process_response to apply it AFTER login completes.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self._remember    = False              # flag carried from request to response

    def __call__(self, request):
        # ── Capture intent on the way IN ──────────────────────────────────────
        if request.method == 'POST' and request.path.endswith('/login/'):
            self._remember = bool(request.POST.get('remember_me'))

        response = self.get_response(request)

        # ── Apply expiry on the way OUT (after auth middleware ran) ───────────
        if request.method == 'POST' and request.path.endswith('/login/'):
            if request.user.is_authenticated:
                request.session.set_expiry(1209600 if self._remember else 0)

        return response
    

class RequirePasswordMiddleware:
    """
    After Google login, if user has no usable password,
    force them to /dashboard/set-password/ on every request.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            set_password_url = reverse('ptfapp2:set_password')
            exempt_urls = [
                set_password_url,
                reverse('ptfapp2:logout'),
            ]
            if (
                not request.user.has_usable_password()
                and request.path not in exempt_urls
            ):
                return redirect(set_password_url)

        return self.get_response(request)    