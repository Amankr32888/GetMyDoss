from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import (
    SiteProfile,
    Skill,
    Project,
    SocialLink,
    ShortLink,
    Contact,
    Document,
    DownloadLog,
    EmailCapture,
)

@admin.register(SiteProfile)
class SiteProfileAdmin(admin.ModelAdmin):          # ✅ FIXED: was wrongly named SiteProfile (same as model)
    list_display = ("full_name", "user", "job_title", "email", "created_at")
    search_fields = ("full_name", "user__username", "email")
    list_filter = ("created_at",)

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "user", "order")
    list_filter = ("category",)
    search_fields = ("name", "user__username")
    ordering = ("user", "order")

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "featured", "order", "created_at")
    list_filter = ("featured", "created_at")
    search_fields = ("title", "user__username", "technologies", "work_profile")
    ordering = ("user", "order", "-created_at")

@admin.register(SocialLink)
class SocialLinkAdmin(admin.ModelAdmin):
    list_display = ("platform", "user", "url", "is_active", "order")
    list_filter = ("platform", "is_active")
    search_fields = ("user__username", "url")
    ordering = ("user", "order")

@admin.register(ShortLink)
class ShortLinkAdmin(admin.ModelAdmin):
    list_display = ("slug", "user", "target_type", "is_active", "click_count", "created_at")
    list_filter = ("target_type", "is_active", "created_at")
    search_fields = ("slug", "user__username")
    ordering = ("-created_at",)

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "user", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("name", "email", "subject", "company_name", "offered_position")
    ordering = ("-created_at",)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "download_count", "created_at")
    list_filter = ("created_at",)
    search_fields = ("title", "user__username")
    ordering = ("-created_at",)

@admin.register(DownloadLog)
class DownloadLogAdmin(admin.ModelAdmin):
    list_display = ("document", "user", "ip_address", "downloaded_at")
    list_filter = ("downloaded_at", "ip_address")
    search_fields = ("document__title", "user__username", "ip_address")
    ordering = ("-downloaded_at",)

@admin.register(EmailCapture)
class EmailCaptureAdmin(admin.ModelAdmin):
    list_display = ("email", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("email", "user__username")
    ordering = ("-created_at",)