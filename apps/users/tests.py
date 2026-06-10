from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import Follow


User = get_user_model()


TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "users-api-tests",
    }
}


@override_settings(CACHES=TEST_CACHES)
class AuthAPITests(APITestCase):
    def test_register_returns_tokens_and_creates_user(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "new@example.com",
                "username": "newuser",
                "name": "New User",
                "password": "StrongPass123!",
                "password2": "StrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="new@example.com").exists())
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])

    def test_register_rejects_mismatched_passwords(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "email": "bad@example.com",
                "username": "baduser",
                "password": "StrongPass123!",
                "password2": "DifferentPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_refresh_change_password_and_logout(self):
        user = User.objects.create_user(
            email="login@example.com",
            username="loginuser",
            password="StrongPass123!",
        )

        login_response = self.client.post(
            "/api/auth/login/",
            {"email": user.email, "password": "StrongPass123!"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", login_response.data)
        self.assertIn("refresh", login_response.data)

        refresh_response = self.client.post(
            "/api/auth/token/refresh/",
            {"refresh": login_response.data["refresh"]},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.data)

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login_response.data['access']}")
        password_response = self.client.post(
            "/api/auth/change-password/",
            {"old_password": "StrongPass123!", "new_password": "NewStrongPass123!"},
            format="json",
        )
        self.assertEqual(password_response.status_code, status.HTTP_200_OK)

        user.refresh_from_db()
        self.assertTrue(user.check_password("NewStrongPass123!"))

        logout_response = self.client.post(
            "/api/auth/logout/",
            {"refresh": refresh_response.data["refresh"]},
            format="json",
        )
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

    def test_logout_requires_valid_refresh_token(self):
        user = User.objects.create_user(
            email="logout@example.com",
            username="logoutuser",
            password="StrongPass123!",
        )
        self.client.force_authenticate(user=user)

        response = self.client.post("/api/auth/logout/", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(CACHES=TEST_CACHES)
class UserAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            username="user",
            name="User",
            password="StrongPass123!",
        )
        self.target = User.objects.create_user(
            email="target@example.com",
            username="target",
            name="Target",
            password="StrongPass123!",
        )

    def test_me_requires_authentication(self):
        response = self.client.get("/api/users/me/")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_and_updates_current_user(self):
        self.client.force_authenticate(user=self.user)

        get_response = self.client.get("/api/users/me/")
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.data["username"], "user")

        patch_response = self.client.patch(
            "/api/users/me/",
            {"name": "Updated User", "bio": "Writing tests.", "website": "https://example.com"},
            format="json",
        )
        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "Updated User")
        self.assertEqual(self.user.bio, "Writing tests.")

    def test_public_profile_includes_follow_state(self):
        Follow.objects.create(follower=self.user, following=self.target)
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/users/target/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_following"])

    def test_follow_unfollow_and_lists(self):
        self.client.force_authenticate(user=self.user)

        follow_response = self.client.post("/api/users/target/follow/")
        self.assertEqual(follow_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Follow.objects.filter(follower=self.user, following=self.target).exists())

        followers_response = self.client.get("/api/users/target/followers/")
        self.assertEqual(followers_response.status_code, status.HTTP_200_OK)
        self.assertEqual(followers_response.data["results"][0]["username"], "user")

        following_response = self.client.get("/api/users/user/following/")
        self.assertEqual(following_response.status_code, status.HTTP_200_OK)
        self.assertEqual(following_response.data["results"][0]["username"], "target")

        unfollow_response = self.client.delete("/api/users/target/follow/")
        self.assertEqual(unfollow_response.status_code, status.HTTP_200_OK)
        self.assertFalse(Follow.objects.filter(follower=self.user, following=self.target).exists())

    def test_follow_self_is_rejected(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post("/api/users/user/follow/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
