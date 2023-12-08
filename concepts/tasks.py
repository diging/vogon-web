

from django.conf import settings
import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGLEVEL)

from concepts.models import Concept
from concepts.lifecycle import ConceptLifecycle, ConceptLifecycleException

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
