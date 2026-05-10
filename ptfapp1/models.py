from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
import os


# ─── File Upload Path Helpers ─────────────────────────────────────────────────

def profile_image_path(instance, filename):
    return f'profile/{instance.user.username}/{filename}'

def cv_path(instance, filename):
    return f'documents/cv/{instance.user.username}/{filename}'

def project_image_path(instance, filename):
    return f'projects/{instance.user.username}/{filename}'

def project_pdf_path(instance, filename):
    return f'projects/{instance.user.username}/docs/{filename}'

def document_path(instance, filename):
    return f'documents/{instance.user.username}/{filename}'


# ─── Custom Validators ────────────────────────────────────────────────────────

def validate_file_size(file):
    """ -> MaxValueValidator does NOT work on FileField (it's for numbers).
       This custom validator correctly checks file size."""
    max_size = 5 * 1024 * 1024  # 5 MB
    if file.size > max_size:
        raise ValidationError(f'File size must not exceed 5 MB. Current size: {file.size // (1024*1024)} MB.')


# ─── Models ───────────────────────────────────────────────────────────────────

class SiteProfile(models.Model):
    THEME_CHOICES = [
        ('feelnova', 'FeelNova — Dark Cosmos'),
        ('aurora',   'Aurora — Deep Forest'),
        ('crimson',  'Crimson — Dark Industrial'),
    ]

    MODE_CHOICES = [
        ('dark', 'Dark'),
        ('gray', 'Gray'),
    ]
    user             = models.OneToOneField(User, on_delete=models.CASCADE, related_name='site_profile')
    full_name        = models.CharField(max_length=200)
    job_title        = models.CharField(max_length=200, blank=True)
    bio              = models.TextField(blank=True, max_length=20000)
    profile_image    = models.ImageField(upload_to=profile_image_path, blank=True, null=True)
    hero_bg_image    = models.ImageField(upload_to=profile_image_path, blank=True, null=True)
    cv_file          = models.FileField(upload_to=cv_path, blank=True, null=True)
    email            = models.EmailField()
    phone            = models.CharField(max_length=20, blank=True)
    address          = models.CharField(max_length=300, blank=True)
    pincode          = models.CharField(max_length=10, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)
    theme      = models.CharField(max_length=30, choices=THEME_CHOICES, default='feelnova')
    theme_mode = models.CharField(max_length=10, choices=MODE_CHOICES,  default='dark')

    def __str__(self):
        return f"{self.full_name} ({self.user.username})"

    def delete(self, *args, **kwargs):
        for field in [self.profile_image, self.hero_bg_image, self.cv_file]:
            if field and os.path.isfile(field.path):   #  DRY: loop instead of repeating
                os.remove(field.path)
        super().delete(*args, **kwargs)
    


class Skill(models.Model):
    CATEGORY_CHOICES = [
        ('technical', 'Technical'),
        ('soft', 'Soft Skill'),
    ]
    user     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skills')
    name     = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='technical')
    order    = models.IntegerField(default=0)

    class Meta:
        ordering      = ['order', 'name']
        unique_together = ['user', 'name']

    def __str__(self):
        return f"{self.name} ({self.category})"


class Project(models.Model):
    user              = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    title             = models.CharField(max_length=200)
    short_description = models.TextField(blank=True)
    full_description  = models.TextField()
    image             = models.ImageField(upload_to=project_image_path, blank=True, null=True)
    pdf_file          = models.FileField(upload_to=project_pdf_path, blank=True, null=True)
    technologies      = models.CharField(max_length=500, help_text="Comma-separated")
    project_url       = models.URLField(blank=True)
    github_url        = models.URLField(blank=True)
    work_profile      = models.CharField(max_length=200, blank=True)
    featured          = models.BooleanField(default=False)
    order             = models.IntegerField(default=0)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title

    def get_tech_list(self):
        return [t.strip() for t in self.technologies.split(',') if t.strip()]

    def delete(self, *args, **kwargs):
        for field in [self.image, self.pdf_file]:         #  DRY: same cleanup pattern
            if field and os.path.isfile(field.path):
                os.remove(field.path)
        super().delete(*args, **kwargs)


class SocialLink(models.Model):
    PLATFORM_CHOICES = [
        ('linkedin',      'LinkedIn'),
        ('github',        'GitHub'),
        ('stackoverflow', 'Stack Overflow'),
        ('twitter',       'Twitter'),
        ('facebook',      'Facebook'),
        ('instagram',     'Instagram'),
        ('youtube',       'YouTube'),
        ('medium',        'Medium'),
        ('behance',       'Behance'),
        ('dribbble',      'Dribbble'),
    ]
    user          = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_links')
    platform      = models.CharField(max_length=50, choices=PLATFORM_CHOICES)
    url           = models.URLField()
    icon_filename = models.CharField(max_length=50, default='link')
    is_active     = models.BooleanField(default=True)
    order         = models.IntegerField(default=0)

    class Meta:
        ordering        = ['order']
        unique_together = ['user', 'platform']

    def __str__(self):
        return f"{self.platform} - {self.user.username}"


class ShortLink(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='short_links')
    slug        = models.SlugField(max_length=50, unique=True)
    target_type = models.CharField(max_length=50, default='portfolio')
    is_active   = models.BooleanField(default=True)
    click_count = models.IntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"/u/{self.user.username}/{self.slug}"

    def get_absolute_url(self):
        return f"/u/{self.user.username}/{self.slug}/"


class Contact(models.Model):
    user             = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    name             = models.CharField(max_length=200)
    email            = models.EmailField()
    subject          = models.CharField(max_length=300)
    company_name     = models.CharField(max_length=200, blank=True)
    offered_position = models.CharField(max_length=600, blank=True)
    message          = models.TextField()
    phone            = models.CharField(max_length=20, blank=True)
    is_read          = models.BooleanField(default=False)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"


class Document(models.Model):
    user           = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    title          = models.CharField(max_length=200)
    file           = models.FileField(
        upload_to=document_path,
        validators=[
            FileExtensionValidator(['pdf', 'doc', 'docx', 'txt', 'xlsx', 'pptx']),
            validate_file_size,    #  -> replaces broken MaxValueValidator
        ]
    )
    download_count = models.IntegerField(default=0)
    created_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        if self.file and os.path.isfile(self.file.path):
            os.remove(self.file.path)
        super().delete(*args, **kwargs)


class DownloadLog(models.Model):
    document      = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='download_logs')
    user          = models.ForeignKey(User, on_delete=models.CASCADE, related_name='download_logs')
    ip_address    = models.GenericIPAddressField()
    downloaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.document.title} - {self.downloaded_at}"


class EmailCapture(models.Model):
    """Stores email when visitor starts filling contact form but doesn't submit."""
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_captures')
    email      = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} - {self.user.username}"