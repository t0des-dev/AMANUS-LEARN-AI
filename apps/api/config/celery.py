import os

from celery import Celery

# Set default Django settings module for celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("amanus_learn_ai")

# Read config from Django settings with 'CELERY_' prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Autodiscover tasks across all registered Django apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
