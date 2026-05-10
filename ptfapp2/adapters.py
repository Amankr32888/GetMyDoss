from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.shortcuts import redirect
from django.urls import reverse


class CustomAccountAdapter(DefaultAccountAdapter):
    """Keeps your existing manual login untouched."""

    def is_open_for_signup(self, request):
        return False


class RequirePasswordSocialAdapter(DefaultSocialAccountAdapter):

    def is_open_for_signup(self, request, sociallogin):
        return True

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        from ptfapp1.models import SiteProfile
        SiteProfile.objects.get_or_create(
            user=user,
            defaults={
                'full_name': user.get_full_name() or user.username,
                'email':     user.email,
            }
        )
        return user

    def get_signup_redirect_url(self, request):
        # ← correct hook for NEW users signing up via Google
        return reverse('ptfapp2:set_password')

    def get_connect_redirect_url(self, request, socialaccount):
        # ← for existing users connecting Google to their account
        return reverse('ptfapp2:set_password')