

from django.conf import settings
import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGLEVEL)

import requests

from concepts.authorities import resolve, search, add
from concepts.models import Concept
from concepts.lifecycle import *

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from celery import shared_task


@shared_task
def resolve_concept(instance_id):
    """
    Since resolving concepts can involve several API calls, we handle it
    asynchronously.
    """
    try:
        manager = ConceptLifecycle(Concept.objects.get(pk=instance_id))
    except Concept.DoesNotExist:
        return

    try:
        manager.resolve()
    except ConceptLifecycleException as E:
        logger.debug("Resolve concept failed: %s" % str(E))
        return 
    logger.debug("Resolved concept %s" % manager.instance.uri)
