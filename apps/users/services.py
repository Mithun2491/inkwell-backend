from django.db import transaction
from django.contrib.auth import get_user_model
from apps.notifications.services import NotificationService

User = get_user_model()


class FollowService:
    """Handles follow/unfollow with atomic counter updates."""

    @staticmethod
    @transaction.atomic
    def follow(follower: User, target: User) -> bool:
        """Returns True if followed, False if already following."""
        from .models import Follow

        if follower == target:
            raise ValueError("You cannot follow yourself.")

        follow, created = Follow.objects.get_or_create(
            follower=follower,
            following=target,
        )

        if created:
            # Update denormalized counters
            User.objects.filter(pk=follower.pk).update(
                following_count=follower.following_count + 1
            )
            User.objects.filter(pk=target.pk).update(
                followers_count=target.followers_count + 1
            )

            # Trigger notification (async)
            NotificationService.notify_follow(actor=follower, target=target)

        return created

    @staticmethod
    @transaction.atomic
    def unfollow(follower: User, target: User) -> bool:
        """Returns True if unfollowed, False if not following."""
        from .models import Follow

        deleted_count, _ = Follow.objects.filter(
            follower=follower, following=target
        ).delete()

        if deleted_count:
            User.objects.filter(pk=follower.pk).update(
                following_count=max(follower.following_count - 1, 0)
            )
            User.objects.filter(pk=target.pk).update(
                followers_count=max(target.followers_count - 1, 0)
            )
            return True

        return False
