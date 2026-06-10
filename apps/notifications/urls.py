from django.urls import path
from .views import NotificationListView, UnreadCountView, MarkAllReadView, MarkReadView

urlpatterns = [
    path("", NotificationListView.as_view(), name="notification-list"),
    path("unread-count/", UnreadCountView.as_view(), name="notification-unread-count"),
    path("mark-all-read/", MarkAllReadView.as_view(), name="notification-mark-all-read"),
    path("<uuid:pk>/read/", MarkReadView.as_view(), name="notification-mark-read"),
]
