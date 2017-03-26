from __future__ import absolute_import

import os

from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vogon.settings')

from django.conf import settings

app = Celery('vogon')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
app.conf.update(BROKER_URL=os.environ.get('REDIS_URL', 'redis://localhost:6379/2'),
                CELERY_RESULT_BACKEND=os.environ.get('REDIS_URL', 'redis://localhost:6379/2'))
