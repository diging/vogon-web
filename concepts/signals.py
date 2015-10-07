from django.db.models.signals import post_save
from django.dispatch import receiver

from .authorities import resolve
from .models import Concept, Type
from concepts.tasks import resolve_concept

import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')

### Handle Concept and Type signals. ###

# @receiver(post_save, sender=Concept)
# def concept_post_save_receiver(sender, **kwargs):
#     """
#     When a :class:`.Concept` is saved, attempt to resolve it using one of the
#     registered :class:`.AuthorityManager` classes if the :class:`.Concept` is
#     not already :prop:`.resolved`\.
#     """
#     instance = kwargs.get('instance', None)
#     resolve_concept.delay(sender, instance)
#
# @receiver(post_save, sender=Type)
# def type_post_save_receiver(sender, **kwargs):
#     """
#     When a :class:`.Type` is saved, attempt to resolve it using one of the
#     registered :class:`.AuthorityManager` classes if the :class:`.Type` is
#     not already :prop:`.resolved`\.
#     """
#     instance = kwargs.get('instance', None)
#     resolve_concept.delay(sender, instance)
