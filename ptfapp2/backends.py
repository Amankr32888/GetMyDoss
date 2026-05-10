from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q


class EmailOrUsernameBackend(ModelBackend):
    """
    Allow users to log in with either their username or email address.
    Registered in settings.py AUTHENTICATION_BACKENDS.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:            # ✅ fast-exit on empty input
            return None

        try:
            # ✅ FIXED: single query with Q instead of two nested try/except blocks
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
        except User.MultipleObjectsReturned:        # ✅ NEW: edge case — two accounts, same email
            # Fall back to exact username match only
            try:
                user = User.objects.get(username__iexact=username)
            except User.DoesNotExist:
                return None
        except User.DoesNotExist:
            return None

        if user.check_password(password) and self.user_can_authenticate(user): # ✅ respects is_active
            return user
        return None

    def get_user(self, user_id):                    # ✅ NEW: required for session auth to work correctly
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None