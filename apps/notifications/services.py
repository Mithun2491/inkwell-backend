from django.contrib.auth import get_user_model

User = get_user_model()


class NotificationService:
    """
    Central service for creating notifications.
    All methods are no-ops if the actor == recipient (no self-notifications).
    These are called synchronously but can be easily moved to Celery tasks.
    """

    @staticmethod
    def _create(recipient, actor, notification_type, message, post_slug="", comment_id=None):
        from .models import Notification
        if recipient == actor:
            return  # No self-notifications
        Notification.objects.create(
            recipient=recipient,
            actor=actor,
            notification_type=notification_type,
            message=message,
            post_slug=post_slug,
            comment_id=comment_id,
        )

    @classmethod
    def notify_follow(cls, actor: User, target: User):
        cls._create(
            recipient=target,
            actor=actor,
            notification_type="follow",
            message=f"{actor.username} started following you.",
        )

    @classmethod
    def notify_like(cls, actor: User, post):
        cls._create(
            recipient=post.author,
            actor=actor,
            notification_type="like_post",
            message=f"{actor.username} liked your post \"{post.title}\".",
            post_slug=post.slug,
        )

    @classmethod
    def notify_comment(cls, actor: User, post, comment):
        if comment.parent:
            # It's a reply — notify the parent comment author
            cls._create(
                recipient=comment.parent.author,
                actor=actor,
                notification_type="reply",
                message=f"{actor.username} replied to your comment.",
                post_slug=post.slug,
                comment_id=comment.id,
            )
        # Also notify the post author (if different from commenter)
        cls._create(
            recipient=post.author,
            actor=actor,
            notification_type="comment",
            message=f"{actor.username} commented on your post \"{post.title}\".",
            post_slug=post.slug,
            comment_id=comment.id,
        )
