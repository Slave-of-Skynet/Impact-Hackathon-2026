from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Account, ChildProfile, Reader, Throttle


@admin.register(Account)
class AccountAdmin(UserAdmin):
    ordering = ["email"]
    list_display = ["email", "display_name", "is_staff", "is_active"]
    search_fields = ["email", "display_name"]
    readonly_fields = ["pin_hash", "last_login", "date_joined"]
    fieldsets = [
        (None, {"fields": ["email", "password", "display_name", "ui_language", "pin_hash"]}),
        ("Permissions", {"fields": ["is_active", "is_staff", "is_superuser", "groups", "user_permissions"]}),
        ("Dates", {"fields": ["last_login", "date_joined"]}),
    ]
    add_fieldsets = [
        (None, {"classes": ["wide"], "fields": ["email", "display_name", "password1", "password2"]}),
    ]


class ReadOnlyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ChildProfile)
class ChildProfileAdmin(ReadOnlyAdmin):
    # authorization.md: staff see children read-only, nickname only; guardians manage them in the app.
    list_display = ["nickname", "age_band", "created_at"]
    fields = ["nickname", "age_band", "created_at"]


@admin.register(Reader)
class ReaderAdmin(ReadOnlyAdmin):
    list_display = ["public_id", "kind"]
    fields = ["public_id", "kind"]


@admin.register(Throttle)
class ThrottleAdmin(ReadOnlyAdmin):
    list_display = ["scope", "failures", "window_started_at", "locked_until"]
    list_filter = ["scope"]
    fields = ["scope", "failures", "window_started_at", "locked_until"]
