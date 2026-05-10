import logging
import json

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, ListView
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.http import FileResponse, Http404, JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings

logger = logging.getLogger(__name__)

from .models import (
    SiteProfile, Skill, Project, SocialLink,
    ShortLink, Contact, Document, DownloadLog, EmailCapture
)
from .forms import ContactForm


# ─── Helpers ──────────────────────────────────────────────────────────────────

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# ═══════════════════════════════════════════════════════════════════════════════
# ─── MAIL PIPELINE ────────────────────────────────────────────────────────────
# Three focused functions composed together in _send_contact_emails().
# Each can be unit-tested or reused for other events independently.
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_mail_ids(contact, profile):
    """
    Step 1 — Resolve who gets mail for this contact-form event.
    SiteProfile.email may be blank; fall back to the Django User's email
    so the portfolio owner always receives a notification.

    Returns:
        { 'owner_email': str | None, 'visitor_email': str }
    """
    # SiteProfile.email takes priority; fall back to the linked User.email
    owner_email = (profile.email or '').strip() or (
        profile.user.email if hasattr(profile, 'user') else ''
    )

    return {
        'owner_email':   owner_email or None,   # None → skipped in mail_sender
        'visitor_email': contact.email,
    }


def mail_composer(event, contact, profile, portfolio_user, base_url):
    """
    Step 2 — Build ready-to-send mail payloads for every recipient.

    Args:
        event          : str  — which trigger ('contact_form')
        contact        : Contact instance
        profile        : SiteProfile instance (portfolio owner)
        portfolio_user : User instance
        base_url       : str  — e.g. 'https://mysite.com/'

    Returns:
        List of dicts, each with keys 'subject', 'body', 'recipients'.
    """
    mails = []

    if event == 'contact_form':

        # ── Mail 1 : To the PORTFOLIO OWNER (site user) ───────────────────────
        mails.append({
            'subject': f"New message from {contact.name}: {contact.subject}",
            'body': (
                f"Hi {profile.full_name},\n\n"
                f"Someone just reached out via your portfolio!\n\n"
                f"{'─' * 40}\n"
                f"Name             : {contact.name}\n"
                f"Email            : {contact.email}\n"
                f"Company          : {contact.company_name or 'N/A'}\n"
                f"Position offered : {contact.offered_position or 'N/A'}\n"
                f"Phone            : {contact.phone or 'N/A'}\n"
                f"Subject          : {contact.subject}\n"
                f"{'─' * 40}\n\n"
                f"Message:\n\n{contact.message}\n\n"
                f"{'─' * 40}\n"
                f"Reply directly to: {contact.email}\n\n"
                f"— Your Portfolio Platform"
            ),
            'recipients': [profile.email],
        })

        # ── Mail 2 : Thank-you to the VISITOR ─────────────────────────────────
        mails.append({
            'subject': f"Thanks for reaching out to {profile.full_name}!",
            'body': (
                f"Hi {contact.name},\n\n"
                f"Thank you for contacting {profile.full_name} through their portfolio.\n"
                f"Your message has been received and they'll get back to you soon.\n\n"
                f"Here's a quick summary of what you sent:\n\n"
                f"  Subject : {contact.subject}\n"
                f"  Message : {contact.message[:200]}"
                f"{'...' if len(contact.message) > 200 else ''}\n\n"
                f"If you have anything to add, visit:\n"
                f"{base_url}u/{portfolio_user.username}/\n\n"
                f"Warm regards,\n{profile.full_name}"
            ),
            'recipients': [contact.email],
        })

    return mails


def mail_sender(mails):
    sent = failed = 0

    for mail in mails:
        # ── Guard: skip if no valid recipients ────────────────────────────────
        recipients = [r for r in mail.get('recipients', []) if r]
        if not recipients:
            logger.warning(
                "Mail SKIPPED  — no valid recipients | subject: %s",
                mail['subject']
            )
            failed += 1
            continue

        try:
            result = send_mail(
                subject        = mail['subject'],
                message        = mail['body'],
                from_email     = settings.DEFAULT_FROM_EMAIL,
                recipient_list = recipients,
                fail_silently  = False,
            )
            logger.info(
                "Mail sent     → %s | subject: %s | result: %d",
                recipients, mail['subject'], result
            )
            sent += 1
        except Exception as e:
            logger.exception(
                "Mail FAILED   → %s | subject: %s | error: %s",
                recipients, mail['subject'], str(e)
            )
            failed += 1

    return {'sent': sent, 'failed': failed}


# ─── Orchestrator ─────────────────────────────────────────────────────────────

def _send_contact_emails(request, contact, profile, portfolio_user):
    """
    Glues the three pipeline stages together for a contact-form event.

        fetch_mail_ids  →  mail_composer  →  mail_sender
    """
    base_url = request.build_absolute_uri('/')

    # 1. Who gets mail?
    ids = fetch_mail_ids(contact, profile)
    logger.info(
        "Contact event  | owner: %s  visitor: %s",
        ids['owner_email'], ids['visitor_email']
    )
    logger.debug(
        "Owner email from profile: %s | Profile: %s",
        profile.email, profile
    )

    # 2. Build payloads
    mails = mail_composer(
        event          = 'contact_form',
        contact        = contact,
        profile        = profile,
        portfolio_user = portfolio_user,
        base_url       = base_url,
    )
    logger.debug("Composed %d emails for sending", len(mails))

    # 3. Send
    result = mail_sender(mails)


# ═══════════════════════════════════════════════════════════════════════════════
# ─── Views ────────────────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class Home_View(View):
    """Single-page portfolio: Hero, About, Skills, Projects, Contact."""

    def _get_context(self, user, form):
        return {
            'profile':           user.site_profile,
            'user_obj':          user,
            'skills_technical':  user.skills.filter(category='technical'),
            'skills_soft':       user.skills.filter(category='soft'),
            'featured_projects': user.projects.filter(featured=True)[:6],
            'social_links':      user.social_links.filter(is_active=True),
            'form':              form,
        }

    def get(self, request, username=None):
        if not username:
            return redirect('ptfapp2:login')
        user = get_object_or_404(User, username=username)
        if not hasattr(user, 'site_profile'):
            raise Http404("Portfolio not found")
        return render(request, 'home.html', self._get_context(user, ContactForm()))

    def post(self, request, username=None):
        if not username:
            return redirect('ptfapp2:login')
        user = get_object_or_404(User, username=username)
        if not hasattr(user, 'site_profile'):
            raise Http404("Portfolio not found")

        profile = user.site_profile
        
        form = ContactForm(request.POST)
        
        if form.is_valid():
            contact      = form.save(commit=False)
            contact.user = user
            contact.save()

            _send_contact_emails(request, contact, profile, portfolio_user=user)

            messages.success(request, "Message sent successfully!")
            return redirect('ptfapp1:home', username=username)

        messages.error(request, "Please correct the errors below.")
        return render(request, 'home.html', self._get_context(user, form))


# ─── Skills ───────────────────────────────────────────────────────────────────

class SkillsListView(ListView):
    model               = Skill
    template_name       = 'skills_list.html'
    context_object_name = 'skills'

    def _get_user(self):
        if not hasattr(self, '_user'):
            self._user = get_object_or_404(User, username=self.kwargs['username'])
        return self._user

    def get_queryset(self):
        return Skill.objects.filter(user=self._get_user())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user    = self._get_user()
        qs      = self.get_queryset()
        context['user_obj']         = user
        context['profile']          = user.site_profile
        context['skills_technical'] = qs.filter(category='technical')
        context['skills_soft']      = qs.filter(category='soft')
        return context


# ─── Projects ─────────────────────────────────────────────────────────────────

class ProjectsListView(ListView):
    model               = Project
    template_name       = 'projects_list.html'
    context_object_name = 'projects'
    paginate_by         = 9

    def _get_user(self):
        if not hasattr(self, '_user'):
            self._user = get_object_or_404(User, username=self.kwargs['username'])
        return self._user

    def get_queryset(self):
        return Project.objects.filter(user=self._get_user())

    def get_context_data(self, **kwargs):
        context            = super().get_context_data(**kwargs)
        user               = self._get_user()
        context['user_obj'] = user
        context['profile'] = user.site_profile
        return context


# ─── Short Link Redirect ──────────────────────────────────────────────────────

class ShortLinkRedirectView(View):
    def get(self, request, username, slug):
        user       = get_object_or_404(User, username=username)
        short_link = get_object_or_404(ShortLink, user=user, slug=slug, is_active=True)
        ShortLink.objects.filter(pk=short_link.pk).update(
            click_count=short_link.click_count + 1
        )
        return redirect('ptfapp1:home', username=username)


# ─── Document Download ────────────────────────────────────────────────────────

class DocumentDownloadView(View):
    def get(self, request, doc_id):
        if not request.user.is_authenticated:
            messages.error(request, "Login required to download documents.")
            return redirect('login')

        document = get_object_or_404(Document, id=doc_id, user=request.user)

        DownloadLog.objects.create(
            document   = document,
            user       = request.user,
            ip_address = get_client_ip(request),
        )
        Document.objects.filter(pk=document.pk).update(
            download_count=document.download_count + 1
        )

        filename = document.file.name.split('/')[-1]
        response = FileResponse(document.file.open('rb'), as_attachment=True)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


# ─── API: Email Capture ───────────────────────────────────────────────────────

@require_POST
def capture_email_view(request):
    try:
        data     = json.loads(request.body)
        email    = data.get('email', '').strip()
        username = data.get('username', '').strip()

        if not email or not username:
            return JsonResponse(
                {'success': False, 'error': 'Email and username are required.'}, status=400
            )

        user = User.objects.filter(username=username).first()
        if not user:
            return JsonResponse({'success': False, 'error': 'User not found.'}, status=404)

        EmailCapture.objects.get_or_create(user=user, email=email)
        return JsonResponse({'success': True})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)