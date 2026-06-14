from __future__ import annotations
from typing import TYPE_CHECKING

from django.db import transaction
from django.core.cache import cache
from django.contrib.auth import get_user_model

from .models import Post, Comment, Like, Bookmark
from apps.notifications.services import NotificationService

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser as User
else:
    User = get_user_model()

VIEW_COUNT_CACHE_TTL = 60 * 5  # 5 minutes before flushing to DB


class PostService:

    @staticmethod
    def publish(post: Post) -> Post:
        from django.utils import timezone
        if post.status == Post.Status.PUBLISHED:
            raise ValueError("Post is already published.")
        post.status = Post.Status.PUBLISHED
        post.published_at = timezone.now()
        post.save(update_fields=["status", "published_at"])
        return post

    @staticmethod
    def record_view(post: Post, user: User = None):
        """
        Increments view count using Redis to batch DB writes.
        Call this every time a post detail is fetched.
        """
        cache_key = f"post_views:{post.pk}"
        count = cache.get(cache_key, 0)
        count += 1
        cache.set(cache_key, count, VIEW_COUNT_CACHE_TTL)

        # Flush to DB every 10 views
        if count % 10 == 0:
            Post.objects.filter(pk=post.pk).update(views_count=Post.objects.get(pk=post.pk).views_count + count)
            cache.delete(cache_key)


class LikeService:

    @staticmethod
    @transaction.atomic
    def toggle_post_like(user: User, post: Post) -> dict:
        like, created = Like.objects.get_or_create(user=user, post=post)
        if created:
            Post.objects.filter(pk=post.pk).update(likes_count=post.likes_count + 1)
            NotificationService.notify_like(actor=user, post=post)
            return {"liked": True, "likes_count": post.likes_count + 1}
        else:
            like.delete()
            new_count = max(post.likes_count - 1, 0)
            Post.objects.filter(pk=post.pk).update(likes_count=new_count)
            return {"liked": False, "likes_count": new_count}

    @staticmethod
    @transaction.atomic
    def toggle_comment_like(user: User, comment: Comment) -> dict:
        like, created = Like.objects.get_or_create(user=user, comment=comment)
        if created:
            Comment.objects.filter(pk=comment.pk).update(likes_count=comment.likes_count + 1)
            return {"liked": True, "likes_count": comment.likes_count + 1}
        else:
            like.delete()
            new_count = max(comment.likes_count - 1, 0)
            Comment.objects.filter(pk=comment.pk).update(likes_count=new_count)
            return {"liked": False, "likes_count": new_count}


class BookmarkService:

    @staticmethod
    @transaction.atomic
    def toggle_bookmark(user: User, post: Post) -> dict:
        bookmark, created = Bookmark.objects.get_or_create(user=user, post=post)
        if created:
            Post.objects.filter(pk=post.pk).update(bookmarks_count=post.bookmarks_count + 1)
            return {"bookmarked": True, "bookmarks_count": post.bookmarks_count + 1}
        else:
            bookmark.delete()
            new_count = max(post.bookmarks_count - 1, 0)
            Post.objects.filter(pk=post.pk).update(bookmarks_count=new_count)
            return {"bookmarked": False, "bookmarks_count": new_count}


class CommentService:

    @staticmethod
    @transaction.atomic
    def create_comment(post: Post, author: User, body: str, parent: Comment = None) -> Comment:
        comment = Comment.objects.create(
            post=post,
            author=author,
            body=body,
            parent=parent,
        )
        Post.objects.filter(pk=post.pk).update(comments_count=post.comments_count + 1)
        NotificationService.notify_comment(actor=author, post=post, comment=comment)
        return comment

    @staticmethod
    @transaction.atomic
    def delete_comment(comment: Comment):
        post = comment.post
        comment.delete()
        Post.objects.filter(pk=post.pk).update(
            comments_count=max(post.comments_count - 1, 0)
        )
