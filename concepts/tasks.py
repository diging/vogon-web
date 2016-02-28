from __future__ import absolute_import

from concepts.authorities import resolve, search

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from celery import shared_task

@shared_task
def resolve_concept(sender, instance):
    resolve(sender, instance)

@shared_task
def search_concept(query, pos='noun'):
    search(query, pos)
