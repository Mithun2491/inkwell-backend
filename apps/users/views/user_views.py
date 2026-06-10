from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from apps.users.serializers import (
    UserProfileSerializer,
    UpdateProfileSerializer,
    UserPublicSerializer,
)
from apps.users.services import FollowService

User = get_user_model()


class MeView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/users/me/      → current user profile
    PATCH /api/users/me/     → update profile
    """
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return UpdateProfileSerializer
        return UserProfileSerializer

    def get_serializer_context(self):
        return {"request": self.request}


class UserProfileView(generics.RetrieveAPIView):
    """GET /api/users/<username>/"""
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    lookup_field = "username"
    queryset = User.objects.filter(is_active=True)

    def get_serializer_context(self):
        return {"request": self.request}


class FollowersListView(generics.ListAPIView):
    """GET /api/users/<username>/followers/"""
    serializer_class = UserPublicSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs["username"])
        return User.objects.filter(following_set__following=user)


class FollowingListView(generics.ListAPIView):
    """GET /api/users/<username>/following/"""
    serializer_class = UserPublicSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs["username"])
        return User.objects.filter(followers_set__follower=user)


class FollowToggleView(APIView):
    """
    POST   /api/users/<username>/follow/   → follow
    DELETE /api/users/<username>/follow/   → unfollow
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request, username):
        target = get_object_or_404(User, username=username, is_active=True)
        try:
            created = FollowService.follow(follower=request.user, target=target)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if created:
            return Response({"message": f"You are now following {username}."}, status=status.HTTP_201_CREATED)
        return Response({"message": f"Already following {username}."})

    def delete(self, request, username):
        target = get_object_or_404(User, username=username, is_active=True)
        unfollowed = FollowService.unfollow(follower=request.user, target=target)
        if unfollowed:
            return Response({"message": f"Unfollowed {username}."})
        return Response({"message": "You were not following this user."})
