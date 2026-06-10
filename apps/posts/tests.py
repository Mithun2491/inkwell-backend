from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.posts.models import Bookmark, Comment, Like, Post
from apps.users.models import Follow


User = get_user_model()


TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "posts-api-tests",
    }
}


@override_settings(CACHES=TEST_CACHES)
class PostAPITests(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            email="author@example.com",
            username="author",
            password="StrongPass123!",
        )
        self.reader = User.objects.create_user(
            email="reader@example.com",
            username="reader",
            password="StrongPass123!",
        )
        self.other = User.objects.create_user(
            email="other@example.com",
            username="other",
            password="StrongPass123!",
        )
        self.published = Post.objects.create(
            author=self.author,
            title="Published Post",
            subtitle="Visible",
            body="A published post body.",
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        self.published.tags.add("django", "api")
        self.draft = Post.objects.create(
            author=self.author,
            title="Draft Post",
            subtitle="Hidden",
            body="A draft post body.",
        )

    def test_list_only_returns_published_posts_with_filters(self):
        response = self.client.get("/api/posts/?tag=django&author=author&search=Published")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["slug"], self.published.slug)

    def test_feed_returns_followed_authors_posts_for_authenticated_user(self):
        Follow.objects.create(follower=self.reader, following=self.author)
        Post.objects.create(
            author=self.other,
            title="Other Published",
            body="Should not be in reader feed.",
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        self.client.force_authenticate(user=self.reader)

        response = self.client.get("/api/posts/feed/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["slug"], self.published.slug)

    def test_create_requires_authentication_and_creates_draft(self):
        anonymous_response = self.client.post(
            "/api/posts/",
            {"title": "New Post", "body": "Body"},
            format="json",
        )
        self.assertEqual(anonymous_response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.reader)
        response = self.client.post(
            "/api/posts/",
            {
                "title": "New Post",
                "subtitle": "Created by API",
                "body": "Body long enough for a reading time.",
                "status": Post.Status.DRAFT,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        post = Post.objects.get(slug="new-post")
        self.assertEqual(post.author, self.reader)
        self.assertEqual(post.status, Post.Status.DRAFT)

    def test_detail_records_view_and_author_can_update_delete(self):
        response = self.client.get(f"/api/posts/{self.published.slug}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Published Post")

        self.client.force_authenticate(user=self.other)
        forbidden_response = self.client.patch(
            f"/api/posts/{self.published.slug}/",
            {"title": "Hacked"},
            format="json",
        )
        self.assertEqual(forbidden_response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.author)
        patch_response = self.client.patch(
            f"/api/posts/{self.published.slug}/",
            {"title": "Updated Published Post"},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)

        delete_response = self.client.delete(f"/api/posts/{self.published.slug}/")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_publish_post_handles_success_and_already_published_error(self):
        self.client.force_authenticate(user=self.author)

        response = self.client.post(f"/api/posts/{self.draft.slug}/publish/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, Post.Status.PUBLISHED)
        self.assertIsNotNone(self.draft.published_at)

        second_response = self.client.post(f"/api/posts/{self.draft.slug}/publish/")
        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mine_lists_current_users_drafts_and_published_posts(self):
        self.client.force_authenticate(user=self.author)

        response = self.client.get("/api/posts/mine/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_like_and_bookmark_toggle_published_post(self):
        self.client.force_authenticate(user=self.reader)

        like_response = self.client.post(f"/api/posts/{self.published.slug}/like/")
        self.assertEqual(like_response.status_code, status.HTTP_200_OK)
        self.assertTrue(like_response.data["liked"])
        self.assertTrue(Like.objects.filter(user=self.reader, post=self.published).exists())

        unlike_response = self.client.post(f"/api/posts/{self.published.slug}/like/")
        self.assertEqual(unlike_response.status_code, status.HTTP_200_OK)
        self.assertFalse(unlike_response.data["liked"])

        bookmark_response = self.client.post(f"/api/posts/{self.published.slug}/bookmark/")
        self.assertEqual(bookmark_response.status_code, status.HTTP_200_OK)
        self.assertTrue(bookmark_response.data["bookmarked"])
        self.assertTrue(Bookmark.objects.filter(user=self.reader, post=self.published).exists())

        bookmarks_response = self.client.get("/api/posts/bookmarks/")
        self.assertEqual(bookmarks_response.status_code, status.HTTP_200_OK)
        self.assertEqual(bookmarks_response.data["results"][0]["slug"], self.published.slug)

        unbookmark_response = self.client.post(f"/api/posts/{self.published.slug}/bookmark/")
        self.assertEqual(unbookmark_response.status_code, status.HTTP_200_OK)
        self.assertFalse(unbookmark_response.data["bookmarked"])


@override_settings(CACHES=TEST_CACHES)
class CommentAPITests(APITestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            email="author2@example.com",
            username="author2",
            password="StrongPass123!",
        )
        self.commenter = User.objects.create_user(
            email="commenter@example.com",
            username="commenter",
            password="StrongPass123!",
        )
        self.other = User.objects.create_user(
            email="other2@example.com",
            username="other2",
            password="StrongPass123!",
        )
        self.post = Post.objects.create(
            author=self.author,
            title="Commented Post",
            body="Body.",
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        self.comment = Comment.objects.create(
            post=self.post,
            author=self.commenter,
            body="First comment",
        )

    def test_list_and_create_comments(self):
        list_response = self.client.get(f"/api/posts/{self.post.slug}/comments/")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data["count"], 1)

        anonymous_response = self.client.post(
            f"/api/posts/{self.post.slug}/comments/",
            {"body": "Anonymous comment"},
            format="json",
        )
        self.assertEqual(anonymous_response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(user=self.other)
        create_response = self.client.post(
            f"/api/posts/{self.post.slug}/comments/",
            {"body": "Second comment"},
            format="json",
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(create_response.data["body"], "Second comment")

    def test_create_reply_and_reject_nested_reply(self):
        self.client.force_authenticate(user=self.other)

        reply_response = self.client.post(
            f"/api/posts/{self.post.slug}/comments/",
            {"body": "A reply", "parent": str(self.comment.id)},
            format="json",
        )
        self.assertEqual(reply_response.status_code, status.HTTP_201_CREATED)
        reply_id = reply_response.data["id"]

        nested_response = self.client.post(
            f"/api/posts/{self.post.slug}/comments/",
            {"body": "Nested reply", "parent": reply_id},
            format="json",
        )
        self.assertEqual(nested_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_comment_detail_update_delete_permissions(self):
        response = self.client.get(f"/api/posts/{self.post.slug}/comments/{self.comment.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.other)
        forbidden_response = self.client.patch(
            f"/api/posts/{self.post.slug}/comments/{self.comment.id}/",
            {"body": "Nope"},
            format="json",
        )
        self.assertEqual(forbidden_response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.commenter)
        patch_response = self.client.patch(
            f"/api/posts/{self.post.slug}/comments/{self.comment.id}/",
            {"body": "Edited comment"},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)

        delete_response = self.client.delete(f"/api/posts/{self.post.slug}/comments/{self.comment.id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_comment_like_toggle(self):
        self.client.force_authenticate(user=self.other)

        like_response = self.client.post(
            f"/api/posts/{self.post.slug}/comments/{self.comment.id}/like/"
        )
        self.assertEqual(like_response.status_code, status.HTTP_200_OK)
        self.assertTrue(like_response.data["liked"])

        unlike_response = self.client.post(
            f"/api/posts/{self.post.slug}/comments/{self.comment.id}/like/"
        )
        self.assertEqual(unlike_response.status_code, status.HTTP_200_OK)
        self.assertFalse(unlike_response.data["liked"])
