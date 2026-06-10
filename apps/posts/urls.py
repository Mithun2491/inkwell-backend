from django.urls import path
from .views import (
    PostFeedView, PostListCreateView, PostDetailView,
    PublishPostView, MyPostsView,
    PostLikeView, PostBookmarkView, MyBookmarksView,
    CommentListCreateView, CommentDetailView, CommentLikeView,
)

urlpatterns = [
    # Feed & Discovery
    path("feed/", PostFeedView.as_view(), name="post-feed"),
    path("", PostListCreateView.as_view(), name="post-list-create"),
    path("mine/", MyPostsView.as_view(), name="my-posts"),
    path("bookmarks/", MyBookmarksView.as_view(), name="my-bookmarks"),

    # Post detail
    path("<slug:slug>/", PostDetailView.as_view(), name="post-detail"),
    path("<slug:slug>/publish/", PublishPostView.as_view(), name="post-publish"),
    path("<slug:slug>/like/", PostLikeView.as_view(), name="post-like"),
    path("<slug:slug>/bookmark/", PostBookmarkView.as_view(), name="post-bookmark"),

    # Comments
    path("<slug:slug>/comments/", CommentListCreateView.as_view(), name="comment-list"),
    path("<slug:slug>/comments/<uuid:id>/", CommentDetailView.as_view(), name="comment-detail"),
    path("<slug:slug>/comments/<uuid:id>/like/", CommentLikeView.as_view(), name="comment-like"),
]
