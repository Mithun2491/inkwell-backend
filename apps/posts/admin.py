from django.contrib import admin

from .models import Bookmark, Comment, Like, Post


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ("author", "body", "likes_count", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("author",)


class LikeInline(admin.TabularInline):
    model = Like
    extra = 0
    fields = ("user", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user",)


class BookmarkInline(admin.TabularInline):
    model = Bookmark
    extra = 0
    fields = ("user", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "status",
        "reading_time",
        "likes_count",
        "comments_count",
        "bookmarks_count",
        "views_count",
        "published_at",
        "created_at",
    )
    list_filter = ("status", "created_at", "published_at", "tags")
    search_fields = ("title", "subtitle", "body", "author__email", "author__username")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("author",)
    readonly_fields = ("id", "reading_time", "created_at", "updated_at")
    date_hierarchy = "created_at"
    inlines = (CommentInline, LikeInline, BookmarkInline)
    fieldsets = (
        ("Content", {"fields": ("title", "slug", "subtitle", "body", "cover_image", "tags")}),
        ("Publishing", {"fields": ("author", "status", "published_at")}),
        ("Stats", {"fields": ("likes_count", "comments_count", "bookmarks_count", "views_count", "reading_time")}),
        ("System", {"fields": ("id", "created_at", "updated_at")}),
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("short_body", "post", "author", "parent", "likes_count", "created_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("body", "post__title", "author__email", "author__username")
    autocomplete_fields = ("post", "author", "parent")
    readonly_fields = ("id", "created_at", "updated_at")

    @admin.display(description="Comment")
    def short_body(self, obj):
        return obj.body[:80]


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("user", "target", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__email", "user__username", "post__title", "comment__body")
    autocomplete_fields = ("user", "post", "comment")
    readonly_fields = ("created_at",)

    @admin.display(description="Target")
    def target(self, obj):
        return obj.post or obj.comment


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("user", "post", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__email", "user__username", "post__title")
    autocomplete_fields = ("user", "post")
    readonly_fields = ("created_at",)
