import django_filters
from .models import Post


class PostFilter(django_filters.FilterSet):
    tag = django_filters.CharFilter(field_name="tags__slug", lookup_expr="iexact")
    author = django_filters.CharFilter(field_name="author__username", lookup_expr="iexact")
    min_reading_time = django_filters.NumberFilter(field_name="reading_time", lookup_expr="gte")
    max_reading_time = django_filters.NumberFilter(field_name="reading_time", lookup_expr="lte")

    class Meta:
        model = Post
        fields = ["tag", "author", "min_reading_time", "max_reading_time"]
