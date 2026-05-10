from django.shortcuts import render

# Create your views here. 
from django.shortcuts import render, redirect, get_object_or_404
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, update_session_auth_hash, authenticate

from django.views import View
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import json
from django.utils.decorators import method_decorator

#for reducing load while deletion operations: 
from django.db import transaction #  to perform deletion operation in background , instead of doing it all at once 


from .forms import (
    CoUserRegistrationForm, ProfileForm, SkillForm,
    ProjectForm, SocialLinkForm, ShortLinkForm, DocumentForm
)
from ptfapp1.models import (                          #  FIXED: was ptfapp
    SiteProfile, Skill, Project, SocialLink,
    ShortLink, EmailCapture, Contact, Document, DownloadLog
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def superuser_required(view_func):
    """ DRY: replaces repeated is_superuser checks inside every co-user view."""
    decorated = user_passes_test(
        lambda u: u.is_superuser,
        login_url='ptfapp2:dashboard'
    )(view_func)
    return decorated


def _delete_old_file(instance_pk, Model, *field_names, request_files):
    """ DRY: delete old file(s) from a model instance when replaced via form."""
    try:
        old = Model.objects.get(pk=instance_pk)
        for field_name in field_names:
            if field_name in request_files:
                old_file = getattr(old, field_name)
                if old_file:
                    old_file.delete(save=False)
    except Model.DoesNotExist:
        pass


# ─── Auth ─────────────────────────────────────────────────────────────────────

def custom_login_view(request):
    """Custom login with remember-me and CSRF protection."""
    if request.user.is_authenticated:             
        return redirect('ptfapp2:dashboard')

    if request.method == 'POST':
        username    = request.POST.get('username', '').strip()
        password    = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me')

        if not username or not password:
            messages.error(request, 'Please provide both username and password.')
            return render(request, 'registration/login.html')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            request.session.set_expiry(1209600 if remember_me else 0)
            messages.success(request, f'Welcome back, {user.username}!')
            next_url = request.GET.get('next') or 'ptfapp2:dashboard'  #  safe fallback
            return redirect(next_url)

        messages.error(request, 'Invalid username or password.')

    return render(request, 'registration/login.html')

@require_POST 
@login_required
def logout_view(request):
    username = request.user.username   # capture BEFORE logout clears it
    logout(request)                    # session ends here
    messages.success(request, f'See you soon, {username}!')
        
    return redirect('ptfapp2:login')

@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)      #  keeps user logged in after change
            messages.success(request, "Password changed successfully!")
            return redirect('ptfapp2:dashboard')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'dashboard/password_change.html', {'form': form})


# ─── Dashboard ────────────────────────────────────────────────────────────────

@login_required
@csrf_protect
def dashboard_view(request):
    user     = request.user
    week_ago = timezone.now() - timedelta(days=7)

    context = {
        'total_documents':     Document.objects.filter(user=user).count(),
        'total_downloads':     DownloadLog.objects.filter(user=user).count(),
        'downloads_this_week': DownloadLog.objects.filter(
                                   user=user, downloaded_at__gte=week_ago
                               ).count(),
        'total_projects':      Project.objects.filter(user=user).count(),
        'total_messages':      Contact.objects.filter(user=user).count(),
        'unread_messages':     Contact.objects.filter(user=user, is_read=False).count(),  #  NEW
        'recent_messages':     Contact.objects.filter(user=user)
                                              .select_related('user')
                                              .order_by('-created_at')[:10],
        'co_users':            User.objects.filter(is_superuser=False, is_staff=False)
                               if user.is_superuser else None,
    }
    return render(request, 'dashboard/dashboard.html', context)


# ─── Profile ──────────────────────────────────────────────────────────────────
@login_required
def profile_page(request):
    """
    Read-only profile overview shown right after login.
    Links to profile_form_view for editing.
    """
    profile      = getattr(request.user, 'site_profile', None)
    social_links = request.user.social_links.filter(is_active=True) if profile else []
    skills       = request.user.skills.all() if profile else []
    projects     = request.user.projects.all() if profile else []
    documents    = Document.objects.filter(user=request.user) if profile else []

    context = {
        'profile':      profile,
        'social_links': social_links,
        'skills':       skills,
        'projects':     projects,
        'documents':    documents,
    }
    return render(request, 'dashboard/profile_page.html', context)

@login_required
def profile_form_view(request):

    profile = getattr(request.user, 'site_profile', None)  #  cleaner than try/except

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            obj      = form.save(commit=False)
            obj.user = request.user

            if obj.pk:                                  # replacing files on existing profile
                _delete_old_file(
                    obj.pk, SiteProfile,
                    'profile_image', 'hero_bg_image', 'cv_file',
                    request_files=request.FILES
                )

            obj.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('ptfapp2:dashboard')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'dashboard/profile_form.html', {'form': form})


# ─── Skills ───────────────────────────────────────────────────────────────────

@login_required
def skills_list_view(request):
    skills = Skill.objects.filter(user=request.user)
    return render(request, 'dashboard/skills_list.html', {'skills': skills})


@login_required
def skill_form_view(request, pk=None):
    skill = get_object_or_404(Skill, pk=pk, user=request.user) if pk else None

    if request.method == 'POST':
        form = SkillForm(request.POST, instance=skill)
        if form.is_valid():
            obj      = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, "Skill saved!")
            return redirect('ptfapp2:skills_list')
    else:
        form = SkillForm(instance=skill)

    return render(request, 'dashboard/skill_form.html', {'form': form, 'object': skill})


@login_required
def skill_delete_view(request, pk):
    skill = get_object_or_404(Skill, pk=pk, user=request.user)
    skill.delete()
    messages.success(request, "Skill deleted!")
    return redirect('ptfapp2:skills_list')


# ─── Projects ─────────────────────────────────────────────────────────────────

@login_required
def projects_list_view(request):
    projects = Project.objects.filter(user=request.user)
    return render(request, 'dashboard/projects_list.html', {'projects': projects})


@login_required
def project_form_view(request, pk=None):
    project = get_object_or_404(Project, pk=pk, user=request.user) if pk else None

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            obj      = form.save(commit=False)
            obj.user = request.user

            if obj.pk:
                _delete_old_file(
                    obj.pk, Project,
                    'image', 'pdf_file',
                    request_files=request.FILES
                )

            obj.save()
            messages.success(request, "Project saved!")
            return redirect('ptfapp2:projects_list')
    else:
        form = ProjectForm(instance=project)
        
        
        
        

    return render(request, 'dashboard/project_form.html', {'form': form, 'object': project})


@login_required
def project_delete_view(request, pk):
    project = get_object_or_404(Project, pk=pk, user=request.user)
    project.delete()
    messages.success(request, "Project deleted!")
    return redirect('ptfapp2:projects_list')


# ─── Social Links ─────────────────────────────────────────────────────────────

@login_required
def social_links_list_view(request):
    links = SocialLink.objects.filter(user=request.user)
    return render(request, 'dashboard/social_links_list.html', {'links': links})


@login_required
def social_link_form_view(request, pk=None):
    link = get_object_or_404(SocialLink, pk=pk, user=request.user) if pk else None

    if request.method == 'POST':
        form = SocialLinkForm(request.POST, instance=link)
        if form.is_valid():
            obj      = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, "Social link saved!")
            return redirect('ptfapp2:social_links_list')
    else:
        form = SocialLinkForm(instance=link)

    return render(request, 'dashboard/social_link_form.html', {'form': form, 'object': link})


@login_required
def social_link_delete_view(request, pk):
    link = get_object_or_404(SocialLink, pk=pk, user=request.user)
    link.delete()
    messages.success(request, "Social link deleted!")
    return redirect('ptfapp2:social_links_list')


# ─── Short Links ──────────────────────────────────────────────────────────────

@login_required
def short_links_list_view(request):
    links = ShortLink.objects.filter(user=request.user)
    return render(request, 'dashboard/short_links_list.html', {'links': links})


@login_required
def short_link_form_view(request, pk=None):
    link = get_object_or_404(ShortLink, pk=pk, user=request.user) if pk else None

    if request.method == 'POST':
        form = ShortLinkForm(request.POST, instance=link)
        if form.is_valid():
            obj      = form.save(commit=False)
            obj.user = request.user
            obj.save()
            messages.success(request, "Short link saved!")
            return redirect('ptfapp2:short_links_list')
    else:
        form = ShortLinkForm(instance=link)

    return render(request, 'dashboard/short_link_form.html', {'form': form, 'object': link})


@login_required
def short_link_delete_view(request, pk):
    link = get_object_or_404(ShortLink, pk=pk, user=request.user)
    link.delete()
    messages.success(request, "Short link deleted!")
    return redirect('ptfapp2:short_links_list')


# ─── Documents ────────────────────────────────────────────────────────────────

@login_required
def documents_list_view(request):
    documents = Document.objects.filter(user=request.user)
    return render(request, 'dashboard/documents_list.html', {'documents': documents})


@login_required
def document_form_view(request, pk=None):
    document = get_object_or_404(Document, pk=pk, user=request.user) if pk else None

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            obj      = form.save(commit=False)
            obj.user = request.user

            if obj.pk:
                _delete_old_file(obj.pk, Document, 'file', request_files=request.FILES)
                messages.info(request, "Old document replaced.")
            else:
                messages.info(request, "New document added.")

            obj.save()
            messages.success(request, "Document saved!")
            return redirect('ptfapp2:documents_list')
    else:
        form = DocumentForm(instance=document)

    return render(request, 'dashboard/document_form.html', {'form': form, 'object': document})


@login_required
def document_delete_view(request, pk):
    document = get_object_or_404(Document, pk=pk, user=request.user)
    document.delete()
    messages.success(request, "Document deleted!")
    return redirect('ptfapp2:documents_list')


# ─── Contact Messages ─────────────────────────────────────────────────────────

@login_required
def messages_list_view(request):
    """Mark messages as read when viewed."""
    qs = Contact.objects.filter(user=request.user).order_by('-created_at')
    Contact.objects.filter(user=request.user, is_read=False).update(is_read=True)  #  bulk mark-read
    return render(request, 'dashboard/messages_list.html', {'messages_list': qs})


# ─── Co-Users (Superuser only) ────────────────────────────────────────────────

@login_required
@superuser_required                                 #  DRY decorator replaces manual checks
def couser_list_view(request):
    co_users = User.objects.filter(is_superuser=False, is_staff=False)
    return render(request, 'dashboard/couser_list.html', {'co_users': co_users})


@login_required
@superuser_required
def couser_form_view(request, pk=None):
    co_user = get_object_or_404(User, pk=pk) if pk else None

    if request.method == 'POST':
        form = CoUserRegistrationForm(request.POST, instance=co_user)
        if form.is_valid():
            form.save()
            messages.success(request, "Co-user saved!")
            return redirect('ptfapp2:couser_list')
    else:
        form = CoUserRegistrationForm(instance=co_user)

    return render(request, 'dashboard/couser_form.html', {'form': form, 'object': co_user})



@login_required
@superuser_required

def couser_delete_view(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    with transaction.atomic():
        # do the deletion inside atomic block
        user.delete()
    
    return redirect('co-users')


# ─── Email Capture API ────────────────────────────────────────────────────────

DISPOSABLE_DOMAINS = {                              #  moved to module level, not rebuilt per request
    'tempmail.com', 'guerrillamail.com', '10minutemail.com',
    'throwaway.email', 'mailinator.com', 'trashmail.com',
}

@require_POST
@csrf_protect
def capture_email_view(request):
    """Capture visitor email when they click CV download."""
    try:
        data     = json.loads(request.body)
        email    = data.get('email', '').strip().lower()
        username = data.get('username', '').strip()

        if not email or not username:
            return JsonResponse(
                {'success': False, 'error': 'Email and username are required.'}, status=400
            )

        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse(
                {'success': False, 'error': 'Please enter a valid email address.'}, status=400
            )

        if email.split('@')[-1] in DISPOSABLE_DOMAINS:
            return JsonResponse(
                {'success': False, 'error': 'Temporary email addresses are not allowed.'}, status=400
            )

        user = User.objects.filter(username=username).first()
        if not user:
            return JsonResponse({'success': False, 'error': 'User not found.'}, status=404)

        _, created = EmailCapture.objects.get_or_create(user=user, email=email)
        return JsonResponse({'success': True, 'already_exists': not created})

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'}, status=500)
    
    
    

class SetPasswordView(View):
    """
    Shown after social signup to force password creation.
    Skipped if user already has a usable password.
    """

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        if request.user.has_usable_password():
            return redirect('ptfapp2:dashboard')
        # pass user_obj so base.html doesn't crash
        return render(request, 'ptfapp2/set_password.html', {
            'user_obj': request.user,
            'profile': getattr(request.user, 'site_profile', None),
        })

    def post(self, request):
        
        password1 = request.POST.get('password1', '').strip()
        password2 = request.POST.get('password2', '').strip()
        
        ctx = {
            'user_obj': request.user,
            'profile': getattr(request.user, 'site_profile', None),
        }
        if not password1 or not password2:
            messages.error(request, "Both fields are required.")
            return render(request, 'ptfapp2/set_password.html', ctx)
        
        if not password1 or not password2:
            messages.error(request, "Both fields are required.")
            return render(request, 'ptfapp2/set_password.html', {
                'user_obj': request.user,
                'profile':  getattr(request.user, 'site_profile', None),
            })

        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'ptfapp2/set_password.html', {
                'user_obj': request.user,
                'profile':  getattr(request.user, 'site_profile', None),
            })

        if len(password1) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return render(request, 'ptfapp2/set_password.html', {
                'user_obj': request.user,
                'profile':  getattr(request.user, 'site_profile', None),
            })

        request.user.set_password(password1)
        request.user.save()
        update_session_auth_hash(request, request.user)   # ← keeps user logged in

        request.session.pop('requires_password_setup', None)
        messages.success(request, "Password set! You're all set.")
        
        return redirect('ptfapp2:dashboard')  
    

 
VALID_THEMES = {'feelnova', 'aurora', 'crimson'}
VALID_MODES  = {'dark', 'gray'}
 
@login_required
@require_POST
def save_theme_view(request):
    try:
        data  = json.loads(request.body)
        theme = data.get('theme', '').strip()
        mode  = data.get('mode', '').strip()
 
        if theme not in VALID_THEMES or mode not in VALID_MODES:
            return JsonResponse({'success': False, 'error': 'Invalid theme or mode.'}, status=400)
 
        profile = request.user.site_profile
        profile.theme      = theme
        profile.theme_mode = mode
        profile.save(update_fields=['theme', 'theme_mode'])
 
        return JsonResponse({'success': True})
 
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
   