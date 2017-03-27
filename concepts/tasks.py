from __future__ import absolute_import

import requests

from concepts.authorities import resolve, search, add
from concepts.models import Concept

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from celery import shared_task


@shared_task
def resolve_concept(sender, instance):
    try:
        resolve(sender, instance)
    except requests.exceptions.ConnectionError:
        pass


@shared_task
def add_concept(sender, instance):
    # try:
    response_data = add(instance)
    instance.uri = response_data['uri']
    instance.concept_state = Concept.RESOLVED
    instance.save()
    # except requests.exceptions.ConnectionError:
    #     pass


@shared_task
def search_concept(query, pos='noun'):
    try:
        search(query, pos)
    except requests.exceptions.ConnectionError:
        pass
