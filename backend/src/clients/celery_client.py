# backend/src/core/celery_app.py
from celery import Celery
from ..core.config import settings

app = Celery(
    "mangoseo",
    broker=settings.celery_broker_url,
    backend=settings.celery_backend_url,
    include=["backend.src.tasks"],
)


app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    worker_max_tasks_per_child=100,
    worker_prefetch_multiplier=1,
)



# . How are we using Celery?

# Celery is for async background jobs → heavy or scheduled tasks outside the request/response lifecycle.

# In your project you already have:

# TaskService → manages tasks metadata (create/update in DB).

# PixelService → deploys SEO/blog changes to user’s site.

# Celery would be useful for:

# Running async jobs (e.g., generating 10k blog posts in the background).

# Scheduling periodic tasks (instead of a cron).

# Offloading deployment steps that can take minutes (PixelService).

# Handling retry logic if an external API (like Webflow/WordPress) fails.

# So → TaskService defines tasks in DB, Celery executes them asynchronously. They’re complementary.

# 4. Are Celery and Redis different?

# Yes 🚦

# Redis = in-memory data store (queue, cache, pub/sub).

# Celery = task queue system. It needs a broker (like Redis or RabbitMQ) to pass messages between producers (FastAPI) and consumers (Celery workers).
# So: Celery is the engine, Redis is the pipeline.

# 5. Upstash Redis vs Celery

# You’re already using Upstash Redis for caching/session storage.

# You can also use the same Redis instance as Celery broker (no need to maintain two).

# Just point CELERY_BROKER_URL to the Upstash Redis connection.

# But beware: Upstash has connection limits & is optimized for caching, not heavy queuing. If your background job volume is huge, a dedicated Redis for Celery may be better.
# 6. Should Celery be included in OnPageSEO (deployment)?

# Yes — that’s a strong candidate.

# PixelService → updates user’s site.

# If 100 users trigger site updates at once → API will bottleneck.

# Better: push jobs into Celery → worker handles them async with retries.

# So Celery is most useful in:

# BlogWriter → generating posts asynchronously.

# OnPageSEO → deploying SEO changes.

# Scheduling recurring jobs → crawl, re-analyze, refresh metrics.