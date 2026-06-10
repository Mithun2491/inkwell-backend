from rest_framework import serializers
from taggit.serializers import TagListSerializerField, TaggitSerializer
from django.utils import timezone

from .models import Post, Comment, Like, Bookmark
from apps.users.serializers import UserPublicSerializer


class PostListSerializer(TaggitSerializer, serializers.ModelSerializer):
    """Lightweight serializer for feed/list views."""
    author = UserPublicSerializer(read_only=True)
    tags = TagListSerializerField()
    cover_image_url = serializers.ReadOnlyField()
    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id", "title", "slug", "subtitle", "cover_image_url",
            "author", "tags", "reading_time", "likes_count",
            "comments_count", "bookmarks_count", "views_count",
            "published_at", "is_liked", "is_bookmarked",
        )

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_is_bookmarked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.bookmarks.filter(user=request.user).exists()
        return False


class PostDetailSerializer(TaggitSerializer, serializers.ModelSerializer):
    """Full post with body — for detail view."""
    author = UserPublicSerializer(read_only=True)
    tags = TagListSerializerField()
    cover_image_url = serializers.ReadOnlyField()
    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id", "title", "slug", "subtitle", "body", "cover_image_url",
            "author", "tags", "reading_time", "status",
            "likes_count", "comments_count", "bookmarks_count", "views_count",
            "published_at", "created_at", "updated_at",
            "is_liked", "is_bookmarked",
        )

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False

    def get_is_bookmarked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.bookmarks.filter(user=request.user).exists()
        return False


class PostWriteSerializer(TaggitSerializer, serializers.ModelSerializer):
    """Used for create/update."""
    tags = TagListSerializerField(required=False)

    class Meta:
        model = Post
        fields = ("title", "subtitle", "body", "cover_image", "status", "tags")

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        post = Post.objects.create(**validated_data)
        if tags:
            post.tags.set(*tags)
        return post

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Auto-set published_at when publishing for the first time
        if validated_data.get("status") == Post.Status.PUBLISHED and not instance.published_at:
            instance.published_at = timezone.now()

        instance.save()
        if tags is not None:
            instance.tags.set(*tags)
        return instance


# ─── Comments ──────────────────────────────────────────────────────────────────

class ReplySerializer(serializers.ModelSerializer):
    author = UserPublicSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "author", "body", "likes_count", "created_at")


class CommentSerializer(serializers.ModelSerializer):
    author = UserPublicSerializer(read_only=True)
    replies = ReplySerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ("id", "author", "body", "parent", "replies", "likes_count", "is_liked", "created_at", "updated_at")
        read_only_fields = ("author", "likes_count", "created_at", "updated_at")

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False


class CommentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("body", "parent")

    def validate_parent(self, parent):
        post_id = self.context.get("post_id")
        if parent and str(parent.post_id) != str(post_id):
            raise serializers.ValidationError("Parent comment does not belong to this post.")
        if parent and parent.parent is not None:
            raise serializers.ValidationError("Cannot reply to a reply.")
        return parent
