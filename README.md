# MediumBlog API — Django + DRF

A production-grade developer blog platform API, similar to Medium.

## Tech Stack
- Django 5 + DRF
- PostgreSQL
- Redis (caching + Celery broker)
- JWT Auth (SimpleJWT)
- django-taggit (tags)
- drf-spectacular (Swagger docs)

---

## Setup

```bash
# 1. Clone and create venv
python -m venv venv && source venv/bin/activate

# 2. Install deps
pip install -r requirements.txt

# 3. Copy env
cp .env.example .env  # fill in your values

# 4. Migrate
python manage.py migrate

# 5. Run
python manage.py runserver

# 6. Swagger docs → http://localhost:8000/api/docs/
```

---

## Project Structure

```
mediumblog/
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
└── apps/
    ├── users/
    │   ├── models.py         ← User, Follow
    │   ├── serializers.py
    │   ├── services.py       ← FollowService
    │   ├── views/
    │   │   ├── auth_views.py
    │   │   └── user_views.py
    │   └── urls/
    │       ├── auth_urls.py
    │       └── user_urls.py
    ├── posts/
    │   ├── models.py         ← Post, Comment, Like, Bookmark
    │   ├── serializers.py
    │   ├── services.py       ← PostService, LikeService, BookmarkService, CommentService
    │   ├── views.py
    │   ├── permissions.py
    │   ├── filters.py
    │   ├── pagination.py
    │   └── urls.py
    └── notifications/
        ├── models.py         ← Notification
        ├── services.py       ← NotificationService
        ├── views.py
        └── urls.py
```

---

## API Endpoints

### Auth — `/api/auth/`
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register/` | Create account |
| POST | `/login/` | Get JWT tokens |
| POST | `/token/refresh/` | Refresh access token |
| POST | `/logout/` | Blacklist refresh token |
| POST | `/change-password/` | Change password |

### Users — `/api/users/`
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/me/` | Current user profile |
| PATCH | `/me/` | Update profile (name, bio, avatar) |
| GET | `/<username>/` | Public profile |
| GET | `/<username>/followers/` | Follower list |
| GET | `/<username>/following/` | Following list |
| POST | `/<username>/follow/` | Follow user |
| DELETE | `/<username>/follow/` | Unfollow user |

### Posts — `/api/posts/`
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/feed/` | Posts from followed authors |
| GET | `/` | All posts (filter, search, sort) |
| POST | `/` | Create post (draft by default) |
| GET | `/mine/` | Your posts (drafts + published) |
| GET | `/bookmarks/` | Your bookmarked posts |
| GET | `/<slug>/` | Post detail |
| PATCH | `/<slug>/` | Edit post |
| DELETE | `/<slug>/` | Delete post |
| POST | `/<slug>/publish/` | Publish a draft |
| POST | `/<slug>/like/` | Toggle like |
| POST | `/<slug>/bookmark/` | Toggle bookmark |

### Comments — `/api/posts/<slug>/comments/`
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List top-level comments + replies |
| POST | `/` | Add comment (or reply via `parent` field) |
| PATCH | `/<id>/` | Edit your comment |
| DELETE | `/<id>/` | Delete comment |
| POST | `/<id>/like/` | Toggle comment like |

### Notifications — `/api/notifications/`
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Paginated notifications |
| GET | `/unread-count/` | Count of unread |
| POST | `/mark-all-read/` | Mark all as read |
| POST | `/<id>/read/` | Mark one as read |

---

## Query Params for Posts

```
GET /api/posts/?tag=python&author=mithun&ordering=-likes_count
GET /api/posts/?search=django+tutorial
GET /api/posts/?min_reading_time=5&max_reading_time=15
GET /api/posts/?page=2&page_size=20
```

---

## Key Design Decisions

**Service Layer** — All business logic (follow, like, bookmark, comment, notify)
lives in `services.py` files. Views are thin controllers.

**Denormalized counters** — `likes_count`, `followers_count` etc. are stored
on the model for O(1) reads instead of expensive COUNT queries on every request.

**Atomic transactions** — All counter updates use `@transaction.atomic` to
prevent race conditions.

**Redis view caching** — View counts are batched in Redis and flushed to DB
every 10 hits, avoiding write-heavy DB load.

**Slug auto-generation** — Post slugs are auto-generated from titles with
collision handling (`my-post`, `my-post-1`, `my-post-2`...).

**Reading time** — Calculated automatically from word count on every save.
