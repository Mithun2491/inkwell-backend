import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Notification(models.Model):
    class Type(models.TextChoices):
        FOLLOW = "follow", "Follow"
        LIKE_POST = "like_post", "Like Post"
        LIKE_COMMENT = "like_comment", "Like Comment"
        COMMENT = "comment", "Comment"
        REPLY = "reply", "Reply"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_notifications")
    notification_type = models.CharField(max_length=20, choices=Type.choices)

    # Optional context (slug/id for deep linking)
    post_slug = models.SlugField(blank=True)
    comment_id = models.UUIDField(null=True, blank=True)

    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient", "is_read"]),
        ]

    def __str__(self):
        return f"[{self.notification_type}] → {self.recipient}"
