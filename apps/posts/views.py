from rest_framework import generics, status, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .models import Post, Comment
from .serializers import (
    PostListSerializer, PostDetailSerializer, PostWriteSerializer,
    CommentSerializer, CommentWriteSerializer,
)
from .services import PostService, LikeService, BookmarkService, CommentService
from .permissions import IsAuthorOrReadOnly
from .filters import PostFilter
from apps.users.models import Follow


class PostFeedView(generics.ListAPIView):
    """
    GET /api/posts/feed/
    Returns posts from authors the current user follows.
    Falls back to latest posts if not authenticated.
    """
    serializer_class = PostListSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            following_ids = Follow.objects.filter(
                follower=self.request.user
            ).values_list("following_id", flat=True)
            return (
                Post.objects.filter(author_id__in=following_ids, status=Post.Status.PUBLISHED)
                .select_related("author")
                .prefetch_related("tags")
            )
        return (
            Post.objects.filter(status=Post.Status.PUBLISHED)
            .select_related("author")
            .prefetch_related("tags")
        )

    def get_serializer_context(self):
        return {"request": self.request}


class PostListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/posts/         → public list with filters
    POST /api/posts/         → create post (auth required)
    """
    permission_classes = (IsAuthenticatedOrReadOnly,)
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filterset_class = PostFilter
    search_fields = ("title", "subtitle", "body", "author__username")
    ordering_fields = ("published_at", "likes_count", "views_count", "reading_time")
    ordering = ("-published_at",)

    def get_queryset(self):
        return (
            Post.objects.filter(status=Post.Status.PUBLISHED)
            .select_related("author")
            .prefetch_related("tags")
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PostWriteSerializer
        return PostListSerializer

    def get_serializer_context(self):
        return {"request": self.request}

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.save(author=request.user)
        return Response(
            PostDetailSerializer(post, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/posts/<slug>/
    PATCH  /api/posts/<slug>/
    DELETE /api/posts/<slug>/
    """
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    lookup_field = "slug"
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        return Post.objects.select_related("author").prefetch_related("tags")

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return PostWriteSerializer
        return PostDetailSerializer

    def get_serializer_context(self):
        return {"request": self.request}

    def retrieve(self, request, *args, **kwargs):
        post = self.get_object()
        PostService.record_view(post, user=request.user if request.user.is_authenticated else None)
        serializer = self.get_serializer(post)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)


class PublishPostView(APIView):
    """POST /api/posts/<slug>/publish/"""
    permission_classes = (IsAuthenticated,)

    def post(self, request, slug):
        post = get_object_or_404(Post, slug=slug, author=request.user)
        try:
            post = PostService.publish(post)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PostDetailSerializer(post, context={"request": request}).data)


class MyPostsView(generics.ListAPIView):
    """GET /api/posts/mine/ — current user's posts (drafts + published)."""
    serializer_class = PostListSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return (
            Post.objects.filter(author=self.request.user)
            .select_related("author")
            .prefetch_related("tags")
            .order_by("-created_at")
        )

    def get_serializer_context(self):
        return {"request": self.request}


# ─── Like / Bookmark ───────────────────────────────────────────────────────────

class PostLikeView(APIView):
    """POST /api/posts/<slug>/like/"""
    permission_classes = (IsAuthenticated,)

    def post(self, request, slug):
        post = get_object_or_404(Post, slug=slug, status=Post.Status.PUBLISHED)
        result = LikeService.toggle_post_like(user=request.user, post=post)
        return Response(result)


class PostBookmarkView(APIView):
    """POST /api/posts/<slug>/bookmark/"""
    permission_classes = (IsAuthenticated,)

    def post(self, request, slug):
        post = get_object_or_404(Post, slug=slug, status=Post.Status.PUBLISHED)
        result = BookmarkService.toggle_bookmark(user=request.user, post=post)
        return Response(result)


class MyBookmarksView(generics.ListAPIView):
    """GET /api/posts/bookmarks/"""
    serializer_class = PostListSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return (
            Post.objects.filter(bookmarks__user=self.request.user, status=Post.Status.PUBLISHED)
            .select_related("author")
            .prefetch_related("tags")
            .order_by("-bookmarks__created_at")
        )

    def get_serializer_context(self):
        return {"request": self.request}


# ─── Comments ──────────────────────────────────────────────────────────────────

class CommentListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/posts/<slug>/comments/
    POST /api/posts/<slug>/comments/
    """
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_post(self):
        return get_object_or_404(Post, slug=self.kwargs["slug"], status=Post.Status.PUBLISHED)

    def get_queryset(self):
        post = self.get_post()
        # Return only top-level comments; replies are nested via serializer
        return (
            Comment.objects.filter(post=post, parent=None)
            .select_related("author")
            .prefetch_related("replies__author")
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CommentWriteSerializer
        return CommentSerializer

    def get_serializer_context(self):
        return {"request": self.request, "post_id": self.get_post().pk}

    def create(self, request, *args, **kwargs):
        post = self.get_post()
        serializer = CommentWriteSerializer(
            data=request.data,
            context={"request": request, "post_id": post.pk},
        )
        serializer.is_valid(raise_exception=True)
        comment = CommentService.create_comment(
            post=post,
            author=request.user,
            body=serializer.validated_data["body"],
            parent=serializer.validated_data.get("parent"),
        )
        return Response(
            CommentSerializer(comment, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/posts/<slug>/comments/<id>/
    PATCH  /api/posts/<slug>/comments/<id>/
    DELETE /api/posts/<slug>/comments/<id>/
    """
    serializer_class = CommentSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly)
    lookup_field = "id"

    def get_queryset(self):
        post = get_object_or_404(Post, slug=self.kwargs["slug"])
        return Comment.objects.filter(post=post).select_related("author")

    def get_serializer_context(self):
        return {"request": self.request}

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        CommentService.delete_comment(comment)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentLikeView(APIView):
    """POST /api/posts/<slug>/comments/<id>/like/"""
    permission_classes = (IsAuthenticated,)

    def post(self, request, slug, id):
        comment = get_object_or_404(Comment, id=id, post__slug=slug)
        result = LikeService.toggle_comment_like(user=request.user, comment=comment)
        return Response(result)
