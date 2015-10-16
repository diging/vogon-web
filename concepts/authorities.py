from .models import Concept, Type

from conceptpower import Conceptpower
from urlparse import urlparse

import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')

class AuthorityManager(object):
    pass

class ConceptpowerAuthority(AuthorityManager, Conceptpower):
    __name__ = 'ConceptpowerAuthority'

    endpoint = 'http://chps.asu.edu/conceptpower/rest/'
    namespace = '{http://www.digitalhps.org/}'

#
# class VogonAuthority(AuthorityManager):
#     __name__ = "VogonAuthority"
#
#     def search(self, query, pos='noun'):
#         return Concept.objects.filter(label__contains=query).filter(pos=pos)
#
#     def get(self, uri):
#         return Concept.object.get(uri=uri)
#
#     def get_type(self, uri):
#         return Type.objects.get(uri=uri)
#
#     namespace = '{http://vogon.asu.edu/}'


# Register AuthorityManagers here.
authority_managers = (
    ConceptpowerAuthority,
    # VogonAuthority,
)

def search(query, pos='noun'):
    results = [r for manager in authority_managers
               for r in manager().search(query, pos=pos)]


    concepts = []
    for r in results:
        r['label'] = r['lemma']
        instance, created = Concept.objects.get_or_create(
                                uri=r['id'],
                                authority=manager.__name__)
        if created:
            instance = update_instance(Concept, instance, r, manager.__name__)
        concepts.append(instance)
    return concepts

def update_instance(sender, instance, concept_data, authority):
    # Update description, label, (and typed).
    instance.description = concept_data['description']

    instance.label = concept_data['label']
    if 'pos' in concept_data:
        instance.pos = concept_data['pos']
    else:
        instance.pos = 'unknown'

    # For Types, this will create a cascade of post_save
    #  signals resulting in a crawl up the Type ontology
    #  based on the ``supertype`` property.
    if sender is Concept:
        if 'type_uri' in concept_data:
            type_uri = concept_data['type_uri']
        else:
            type_uri = None
    elif sender is Type:
        if 'supertype_uri' in concept_data:
            type_uri = concept_data['supertype_uri']
        else:
            type_uri = None

    if type_uri is not None:
        type_instance = Type.objects.get_or_create(uri=type_uri, authority=authority)[0]
        instance.typed = type_instance
        logger.debug(
            'Added Type {0} to Concept {1}.'.format(
                            type_instance.uri, instance.uri))
    instance.save()
    return instance

def resolve(sender, instance):
    """
    Resolve :class:`.Concept`\s and :class:`.Type`\s using the registered
    :class:`.AuthorityManager`\s.

    Parameters
    ----------
    sender : class
    instance : :class:`.Type` or :class:`.Concept`
    """

    logger.debug(
        'Received post_save signal for Concept {0}.'.format(instance.id))

    if instance is not None:
        # Configure based on sender model class.
        instance_cast = instance.cast()
        if type(instance_cast) is Concept:
            get_method = 'get'
            label_field = 'lemma'
        elif type(instance_cast) is Type:
            get_method = 'get_type'
            label_field = 'type'

        # Skip any instance that has already been resolved, or that lacks a URI.
        if not instance.resolved and instance.uri is not None:
            logger.debug('Instance {0} not yet resolved.'.format(instance.id))

            # Get AuthorityManager classes by namespace.
            managers = get_by_namespace(get_namespace(instance.uri))
            logger.debug(
                'Found {0} managers for {1}'.format(len(managers),instance.uri))

            # Try each AuthorityManager...
            for manager_class in managers:
                if instance.resolved: break # ...until success.


                manager = manager_class()
                method = getattr(manager, get_method)
                concept_data = method(instance.uri)
                concept_data['label'] = concept_data[label_field]
                instance.authority = manager.__name__

                logger.debug(
                    'Trying AuthorityManager {0}.'.format(manager.__name__))

                instance.resolved = True
                update_instance(sender, instance, concept_data, manager.__name__)



def get_namespace(uri):
    """
    Extract namespace from URI.
    """

    o = urlparse(uri)
    namespace = o.scheme + "://" + o.netloc + "/"

    if o.scheme == '' or o.netloc == '':
        raise ValueError("Could not determine namespace for {0}.".format(uri))

    return "{" + namespace + "}"

def get_by_namespace(namespace):
    """
    Retrieve a registered :class:`AuthorityManager` by its namespace.
    """

    return [ manager for manager in authority_managers
                if manager.namespace == namespace ]
