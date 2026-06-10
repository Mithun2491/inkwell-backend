from django.urls import path
from apps.users.views.user_views import (
    MeView,
    UserProfileView,
    FollowersListView,
    FollowingListView,
    FollowToggleView,
)

urlpatterns = [
    path("me/", MeView.as_view(), name="user-me"),
    path("<str:username>/", UserProfileView.as_view(), name="user-profile"),
    path("<str:username>/followers/", FollowersListView.as_view(), name="user-followers"),
    path("<str:username>/following/", FollowingListView.as_view(), name="user-following"),
    path("<str:username>/follow/", FollowToggleView.as_view(), name="user-follow"),
]
