import uuid
import math
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from taggit.managers import TaggableManager
from taggit.models import GenericUUIDTaggedItemBase, TaggedItemBase

User = get_user_model()

WORDS_PER_MINUTE = 200


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    subtitle = models.CharField(max_length=300, blank=True)
    body = models.TextField()                         # Rich text / markdown content
    cover_image = models.ImageField(upload_to="covers/", blank=True, null=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    tags = TaggableManager(through="TaggedPost", blank=True)

    # Denormalized stats for performance (updated via signals/services)
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    bookmarks_count = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)
    reading_time = models.PositiveSmallIntegerField(default=1)  # in minutes

    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "posts"
        ordering = ["-published_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["author", "status"]),
            models.Index(fields=["-published_at"]),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        self.reading_time = self._calculate_reading_time()
        super().save(*args, **kwargs)

    def _generate_unique_slug(self):
        base_slug = slugify(self.title)
        slug = base_slug
        counter = 1
        while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def _calculate_reading_time(self):
        word_count = len(self.body.split())
        return max(1, math.ceil(word_count / WORDS_PER_MINUTE))

    @property
    def cover_image_url(self):
        return self.cover_image.url if self.cover_image else None


class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )
    body = models.TextField(max_length=2000)
    likes_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "comments"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["post", "parent"]),
        ]

    def __str__(self):
        return f"Comment by {self.author} on {self.post}"

    @property
    def is_reply(self):
        return self.parent is not None


class TaggedPost(GenericUUIDTaggedItemBase, TaggedItemBase):
    pass


class Like(models.Model):
    """Polymorphic-style likes — can like a post or a comment."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes", null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name="likes", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "likes"
        # Each user can only like a post once
        constraints = [
            models.UniqueConstraint(fields=["user", "post"], condition=models.Q(post__isnull=False), name="unique_post_like"),
            models.UniqueConstraint(fields=["user", "comment"], condition=models.Q(comment__isnull=False), name="unique_comment_like"),
        ]

    def __str__(self):
        target = f"post:{self.post_id}" if self.post_id else f"comment:{self.comment_id}"
        return f"{self.user} liked {target}"


class Bookmark(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookmarks")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="bookmarks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "bookmarks"
        unique_together = ("user", "post")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} bookmarked {self.post}"
