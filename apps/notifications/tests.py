from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.notifications.models import Notification


User = get_user_model()


TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "notifications-api-tests",
    }
}


@override_settings(CACHES=TEST_CACHES)
class NotificationAPITests(APITestCase):
    def setUp(self):
        self.recipient = User.objects.create_user(
            email="recipient@example.com",
            username="recipient",
            password="StrongPass123!",
        )
        self.actor = User.objects.create_user(
            email="actor@example.com",
            username="actor",
            password="StrongPass123!",
        )
        self.other = User.objects.create_user(
            email="other-notify@example.com",
            username="othernotify",
            password="StrongPass123!",
        )
        self.notification = Notification.objects.create(
            recipient=self.recipient,
            actor=self.actor,
            notification_type=Notification.Type.FOLLOW,
            message="actor started following you.",
        )
        Notification.objects.create(
            recipient=self.other,
            actor=self.actor,
            notification_type=Notification.Type.FOLLOW,
            message="actor started following someone else.",
        )

    def test_notification_endpoints_require_authentication(self):
        urls = [
            "/api/notifications/",
            "/api/notifications/unread-count/",
            "/api/notifications/mark-all-read/",
            f"/api/notifications/{self.notification.id}/read/",
        ]

        for url in urls:
            response = self.client.get(url) if url.endswith(("notifications/", "unread-count/")) else self.client.post(url)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_only_returns_current_users_notifications(self):
        self.client.force_authenticate(user=self.recipient)

        response = self.client.get("/api/notifications/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], str(self.notification.id))

    def test_unread_count_mark_read_and_mark_all_read(self):
        Notification.objects.create(
            recipient=self.recipient,
            actor=self.actor,
            notification_type=Notification.Type.COMMENT,
            message="actor commented on your post.",
        )
        self.client.force_authenticate(user=self.recipient)

        count_response = self.client.get("/api/notifications/unread-count/")
        self.assertEqual(count_response.status_code, status.HTTP_200_OK)
        self.assertEqual(count_response.data["unread_count"], 2)

        mark_one_response = self.client.post(f"/api/notifications/{self.notification.id}/read/")
        self.assertEqual(mark_one_response.status_code, status.HTTP_200_OK)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

        mark_all_response = self.client.post("/api/notifications/mark-all-read/")
        self.assertEqual(mark_all_response.status_code, status.HTTP_200_OK)
        self.assertEqual(mark_all_response.data["marked_read"], 1)

    def test_mark_read_returns_not_found_for_other_users_notification(self):
        self.client.force_authenticate(user=self.other)

        response = self.client.post(f"/api/notifications/{self.notification.id}/read/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
