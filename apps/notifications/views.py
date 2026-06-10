from rest_framework import serializers, generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.urls import path

from .models import Notification
from apps.users.serializers import UserPublicSerializer


# ─── Serializer ────────────────────────────────────────────────────────────────

class NotificationSerializer(serializers.ModelSerializer):
    actor = UserPublicSerializer(read_only=True)

    class Meta:
        model = Notification
        fields = (
            "id", "actor", "notification_type", "message",
            "post_slug", "comment_id", "is_read", "created_at",
        )


# ─── Views ─────────────────────────────────────────────────────────────────────

class NotificationListView(generics.ListAPIView):
    """GET /api/notifications/ — paginated notifications for current user."""
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return (
            Notification.objects.filter(recipient=self.request.user)
            .select_related("actor")
        )


class UnreadCountView(APIView):
    """GET /api/notifications/unread-count/"""
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()
        return Response({"unread_count": count})


class MarkAllReadView(APIView):
    """POST /api/notifications/mark-all-read/"""
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        updated = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).update(is_read=True)
        return Response({"marked_read": updated})


class MarkReadView(APIView):
    """POST /api/notifications/<id>/read/"""
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        updated = Notification.objects.filter(
            pk=pk, recipient=request.user
        ).update(is_read=True)
        if not updated:
            return Response({"error": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response({"status": "marked as read"})
