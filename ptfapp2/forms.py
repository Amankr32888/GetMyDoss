from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

from ptfapp1.models import (                        #  FIXED: was ptfapp
    SiteProfile, Skill, Project,
    SocialLink, ShortLink, Document
)


# ─── Shared widget helper ─────────────────────────────────────────────────────

def fc(extra=None):
    """ DRY: returns {'class': 'form-control'} merged with any extra attrs."""
    attrs = {'class': 'form-control'}
    if extra:
        attrs.update(extra)
    return attrs


# ─── Forms ────────────────────────────────────────────────────────────────────

class CoUserRegistrationForm(UserCreationForm):
    email    = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs=fc({'placeholder': 'user@email.com'}))
    )
    username = forms.CharField(
        max_length=9,
        help_text="Exactly 9 characters: lowercase letters and/or numbers (e.g. john00123)",
        widget=forms.TextInput(attrs=fc({'placeholder': 'john00123'}))
    )

    class Meta:
        model  = User
        fields = ['username', 'email', 'password1', 'password2']

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if len(username) != 9:
            raise forms.ValidationError("Username must be exactly 9 characters.")
        if not username.islower() and not username.isdigit():   #  FIXED: pure digits were wrongly rejected
            if username != username.lower():
                raise forms.ValidationError("Username must be lowercase only.")
        if not username.isalnum():                              #  NEW: block special chars
            raise forms.ValidationError("Username may only contain letters and numbers.")
        return username

    def clean_email(self):                                      #  NEW: prevent duplicate emails
        email = self.cleaned_data['email'].lower().strip()
        qs    = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email


class ProfileForm(forms.ModelForm):
    class Meta:
        model  = SiteProfile
        fields = [
            'full_name', 'job_title', 'bio',
            'profile_image', 'hero_bg_image', 'cv_file',
            'email', 'phone', 'address', 'pincode',
        ]
        widgets = {
            'full_name':     forms.TextInput(attrs=fc({'placeholder': 'Your full name'})),
            'job_title':     forms.TextInput(attrs=fc({'placeholder': 'e.g. Full Stack Developer'})),
            'bio':           forms.Textarea(attrs=fc({'rows': 6, 'placeholder': 'Write a short bio...'})),
            'profile_image': forms.FileInput(attrs=fc({'accept': 'image/*'})),
            'hero_bg_image': forms.FileInput(attrs=fc({'accept': 'image/*'})),
            'cv_file':       forms.FileInput(attrs=fc({'accept': '.pdf,.doc,.docx'})),
            'email':         forms.EmailInput(attrs=fc({'placeholder': 'contact@email.com'})),
            'phone':         forms.TextInput(attrs=fc({'placeholder': '+91 XXXXX XXXXX'})),
            'address':       forms.TextInput(attrs=fc({'placeholder': 'City, State'})),
            'pincode':       forms.TextInput(attrs=fc({'placeholder': '4XXXXX', 'maxlength': '10'})),
        }

    def clean_bio(self):                                        # warn if bio too short
        bio = self.cleaned_data.get('bio', '').strip()
        if bio and len(bio) < 20:
            raise forms.ValidationError("Bio is too short. Write at least 20 characters.")
        return bio


class SkillForm(forms.ModelForm):
    class Meta:
        model  = Skill
        fields = ['name', 'category', 'order']
        widgets = {
            'name':     forms.TextInput(attrs=fc({'placeholder': 'e.g. Django'})),
            'category': forms.Select(attrs=fc()),
            'order':    forms.NumberInput(attrs=fc({'min': '0'})),
        }


class ProjectForm(forms.ModelForm):
    class Meta:
        model  = Project
        fields = [
            'title', 'short_description', 'full_description',
            'image', 'pdf_file', 'technologies',
            'project_url', 'github_url', 'work_profile',
            'featured', 'order',
        ]
        widgets = {
            'title':             forms.TextInput(attrs=fc({'placeholder': 'Project title'})),
            'short_description': forms.Textarea(attrs=fc({'rows': 3, 'placeholder': 'One-liner summary'})),
            'full_description':  forms.Textarea(attrs=fc({'rows': 6, 'placeholder': 'Full project description'})),
            'image':             forms.FileInput(attrs=fc({'accept': 'image/*'})),
            'pdf_file':          forms.FileInput(attrs=fc({'accept': '.pdf'})),
            'technologies':      forms.TextInput(attrs=fc({'placeholder': 'Python, Django, React'})),
            'project_url':       forms.URLInput(attrs=fc({'placeholder': 'https://...'})),
            'github_url':        forms.URLInput(attrs=fc({'placeholder': 'https://github.com/...'})),
            'work_profile':      forms.TextInput(attrs=fc({'placeholder': 'e.g. Backend Developer'})),
            'featured':          forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order':             forms.NumberInput(attrs=fc({'min': '0'})),
        }

    def clean_technologies(self):                               #  NEW: normalize comma list
        raw   = self.cleaned_data.get('technologies', '')
        techs = [t.strip() for t in raw.split(',') if t.strip()]
        if not techs:
            raise forms.ValidationError("Please enter at least one technology.")
        return ', '.join(techs)                                 # normalized: "Python, Django, React"


class SocialLinkForm(forms.ModelForm):
    class Meta:
        model  = SocialLink
        fields = ['platform', 'url', 'icon_filename', 'is_active', 'order']
        widgets = {
            'platform':      forms.Select(attrs=fc()),
            'url':           forms.URLInput(attrs=fc({'placeholder': 'https://linkedin.com/in/you'})),
            'icon_filename': forms.TextInput(attrs=fc({'placeholder': 'linkedin'})),
            'is_active':     forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order':         forms.NumberInput(attrs=fc({'min': '0'})),
        }


class ShortLinkForm(forms.ModelForm):
    class Meta:
        model  = ShortLink
        fields = ['slug', 'target_type', 'is_active']
        widgets = {
            'slug':        forms.TextInput(attrs=fc({'placeholder': 'resume'})),
            'target_type': forms.TextInput(attrs=fc({'placeholder': 'portfolio'})),
            'is_active':   forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_slug(self):                                       #  NEW: enforce slug format
        slug = self.cleaned_data['slug'].strip().lower()
        if not slug.replace('-', '').isalnum():
            raise forms.ValidationError("Slug may only contain letters, numbers, and hyphens.")
        return slug


class DocumentForm(forms.ModelForm):
    class Meta:
        model  = Document
        fields = ['title', 'file']
        widgets = {
            'title': forms.TextInput(attrs=fc({'placeholder': 'e.g. My Resume'})),
            'file':  forms.FileInput(attrs=fc({
                'accept': '.pdf,.doc,.docx,.txt,.xlsx,.pptx'
            })),
        }