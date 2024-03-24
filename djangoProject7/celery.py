from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject7.settings')

app = Celery('djangoProject7', node='celery@nikita-Nitro-AN515-45')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
