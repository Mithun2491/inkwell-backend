from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "actor", "notification_type", "message", "is_read", "created_at")
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = ("recipient__email", "recipient__username", "actor__email", "actor__username", "message", "post_slug")
    autocomplete_fields = ("recipient", "actor")
    readonly_fields = ("id", "created_at")
    fieldsets = (
        ("People", {"fields": ("recipient", "actor")}),
        ("Notification", {"fields": ("notification_type", "message", "is_read")}),
        ("Context", {"fields": ("post_slug", "comment_id")}),
        ("System", {"fields": ("id", "created_at")}),
    )
