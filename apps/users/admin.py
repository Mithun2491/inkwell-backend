from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Follow, User


class FollowingInline(admin.TabularInline):
    model = Follow
    fk_name = "follower"
    extra = 0
    autocomplete_fields = ("following",)
    readonly_fields = ("created_at",)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        "email",
        "username",
        "name",
        "is_staff",
        "is_active",
        "followers_count",
        "following_count",
        "date_joined",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "date_joined")
    search_fields = ("email", "username", "name")
    ordering = ("-date_joined",)
    readonly_fields = ("id", "date_joined", "last_login")
    inlines = (FollowingInline,)

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Profile", {"fields": ("name", "bio", "avatar", "website")}),
        ("Stats", {"fields": ("followers_count", "following_count")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        ("System", {"fields": ("id",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "password1", "password2", "is_staff", "is_superuser"),
            },
        ),
    )


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("follower", "following", "created_at")
    search_fields = ("follower__email", "follower__username", "following__email", "following__username")
    list_filter = ("created_at",)
    autocomplete_fields = ("follower", "following")
    readonly_fields = ("created_at",)
