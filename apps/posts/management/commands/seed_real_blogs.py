from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from apps.posts.models import Post


REAL_BLOGS = [
    {
        "title": "Introducing GPT-5 for developers",
        "subtitle": "OpenAI's API launch post for GPT-5, focused on coding, agentic tasks, custom tools, verbosity, and reasoning effort controls.",
        "source": "OpenAI",
        "author": "OpenAI",
        "url": "https://openai.com/index/introducing-gpt-5-for-developers/",
        "published_at": "2025-08-07T09:00:00+00:00",
        "tags": ["genai", "openai", "agents", "coding"],
        "summary": "OpenAI introduces GPT-5 in the API platform as a model aimed at coding and agentic workflows. The post covers benchmark results, custom tool calls, controllable verbosity, minimal reasoning effort, and practical guidance for developers building with GPT-5.",
    },
    {
        "title": "New tools for building agents",
        "subtitle": "OpenAI's announcement of the Responses API, built-in tools, and Agents SDK for production-grade agent workflows.",
        "source": "OpenAI",
        "author": "OpenAI",
        "url": "https://openai.com/index/new-tools-for-building-agents/",
        "published_at": "2025-03-11T09:00:00+00:00",
        "tags": ["genai", "agents", "openai", "api"],
        "summary": "This OpenAI product post introduces building blocks for reliable agents, including the Responses API, web search, file search, computer use, and the Agents SDK. It is useful background for developers moving from simple chat workflows into tool-using AI systems.",
    },
    {
        "title": "Introducing GPT-4.1 in the API",
        "subtitle": "A developer-focused OpenAI post on GPT-4.1, GPT-4.1 mini, and GPT-4.1 nano.",
        "source": "OpenAI",
        "author": "OpenAI",
        "url": "https://openai.com/index/gpt-4-1/",
        "published_at": "2025-04-14T09:00:00+00:00",
        "tags": ["genai", "openai", "api", "long-context"],
        "summary": "OpenAI announces the GPT-4.1 model family for API users, emphasizing improvements in coding, instruction following, long-context use, and lower-cost model options. The post also explains migration timing away from GPT-4.5 Preview.",
    },
    {
        "title": "Introducing gpt-oss",
        "subtitle": "OpenAI's release post for gpt-oss-120b and gpt-oss-20b open-weight reasoning models.",
        "source": "OpenAI",
        "author": "OpenAI",
        "url": "https://openai.com/index/introducing-gpt-oss/",
        "published_at": "2025-08-05T09:00:00+00:00",
        "tags": ["genai", "open-models", "reasoning", "openai"],
        "summary": "OpenAI presents two open-weight reasoning models, gpt-oss-120b and gpt-oss-20b, designed for efficient deployment, tool use, and local or self-hosted experimentation. The post covers architecture details, safety testing, availability, and ecosystem partners.",
    },
    {
        "title": "Python Gains frozendict and Other Python News for March 2026",
        "subtitle": "Real Python's monthly roundup covering Python 3.15 work, security updates, and AI SDK movement.",
        "source": "Real Python",
        "author": "Philipp Acsany",
        "url": "https://realpython.com/python-news-march-2026/",
        "published_at": "2026-03-09T09:00:00+00:00",
        "tags": ["python", "news", "genai", "django"],
        "summary": "Real Python recaps a busy Python month, including PEP 814's accepted frozendict proposal, Python 3.15 alpha work, Django security fixes, uv updates, and AI tooling changes across OpenAI, Anthropic, vLLM, and Wagtail.",
    },
    {
        "title": "Python 3.14: Lazy Annotations",
        "subtitle": "A Real Python deep dive into Python 3.14's deferred annotation evaluation.",
        "source": "Real Python",
        "author": "Bartosz Zaczynski",
        "url": "https://realpython.com/python-annotations/",
        "published_at": "2025-08-27T09:00:00+00:00",
        "tags": ["python", "typing", "python-3-14"],
        "summary": "This Real Python tutorial explains lazy annotations in Python 3.14, why annotation evaluation changes matter, and how the feature affects startup time, forward references, type checking, and runtime metadata handling.",
    },
    {
        "title": "A Close Look at a FastAPI Example Application",
        "subtitle": "A Real Python FastAPI tutorial covering endpoints, Pydantic models, async handlers, CORS, and automatic docs.",
        "source": "Real Python",
        "author": "Philipp Acsany",
        "url": "https://realpython.com/fastapi-python-web-apis/",
        "published_at": "2025-11-03T09:00:00+00:00",
        "tags": ["fastapi", "python", "api", "web-dev"],
        "summary": "Real Python walks through a FastAPI example app that demonstrates path and query parameters, request bodies, Pydantic validation, asynchronous endpoints, CORS configuration, and documentation generated by Swagger UI and ReDoc.",
    },
    {
        "title": "Django 6.0 alpha 1 released",
        "subtitle": "The official Django weblog announcement for the first Django 6.0 alpha release.",
        "source": "Django",
        "author": "Natalia Bidart",
        "url": "https://www.djangoproject.com/weblog/2025/sep/17/django-60-alpha-released/",
        "published_at": "2025-09-17T09:00:00+00:00",
        "tags": ["django", "release", "python"],
        "summary": "The Django project announces Django 6.0 alpha 1, marking the first stage of the 6.0 release cycle and feature freeze. The post encourages early testing while making clear the alpha is not intended for production use.",
    },
    {
        "title": "Django 5.2 release notes",
        "subtitle": "Official Django documentation for the Django 5.2 long-term support release.",
        "source": "Django Documentation",
        "author": "Django Software Foundation",
        "url": "https://docs.djangoproject.com/en/5.2/releases/5.2/",
        "published_at": "2025-04-02T09:00:00+00:00",
        "tags": ["django", "python", "release", "lts"],
        "summary": "The Django 5.2 release notes document the framework's LTS release, including Python compatibility, notable new features, backward-incompatible changes, deprecations, and upgrade guidance for teams moving from Django 5.1 or earlier.",
    },
    {
        "title": "Django REST framework 3.16",
        "subtitle": "The official DRF 3.16 announcement covering Django 5.1, Django 5.2, Python 3.13, and UniqueConstraint support.",
        "source": "Django REST framework",
        "author": "Django REST framework maintainers",
        "url": "https://www.django-rest-framework.org/community/3.16-announcement/",
        "published_at": "2025-03-28T09:00:00+00:00",
        "tags": ["django-rest-framework", "django", "api", "python"],
        "summary": "The DRF maintainers announce REST framework 3.16 with updated Django and Python support, compatibility notes for Django's LoginRequiredMiddleware, improved UniqueConstraint validation, and a pointer to the complete release notes.",
    },
]


def parse_datetime(value):
    parsed = datetime.fromisoformat(value)
    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone=timezone.utc)
    return parsed


def build_body(blog):
    return (
        f"Source: {blog['source']}\n"
        f"Original author: {blog['author']}\n"
        f"Original URL: {blog['url']}\n\n"
        f"{blog['summary']}\n\n"
        "This local entry is seeded from a real published technical article. "
        "Read the original source for the complete post."
    )


class Command(BaseCommand):
    help = "Seed the database with 10 real technology blog entries."

    def handle(self, *args, **options):
        User = get_user_model()
        author, _ = User.objects.update_or_create(
            email="tech-editorial-desk@example.com",
            defaults={
                "username": "tech_editorial_desk",
                "name": "Tech Editorial Desk",
                "bio": "Curated real-world technology posts for the MediumBlog API demo.",
                "website": "https://example.com/tech-editorial-desk",
                "is_active": True,
            },
        )
        author.set_unusable_password()
        author.save(update_fields=["password"])

        created = 0
        updated = 0

        for blog in REAL_BLOGS:
            slug = slugify(blog["title"])
            post, was_created = Post.objects.update_or_create(
                slug=slug,
                defaults={
                    "author": author,
                    "title": blog["title"],
                    "subtitle": blog["subtitle"],
                    "body": build_body(blog),
                    "status": Post.Status.PUBLISHED,
                    "published_at": parse_datetime(blog["published_at"]),
                    "views_count": 250 + (len(blog["title"]) * 17),
                    "likes_count": 25 + len(blog["tags"]) * 9,
                    "bookmarks_count": 8 + len(blog["source"]) % 11,
                    "comments_count": 2 + len(blog["author"]) % 6,
                },
            )
            post.tags.set(blog["tags"])
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(REAL_BLOGS)} real blogs: {created} created, {updated} updated."
            )
        )
