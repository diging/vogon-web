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

# Register AuthorityManagers here.
authority_managers = (
    ConceptpowerAuthority,
)


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

                try:
                    manager = manager_class()
                    method = getattr(manager, get_method)
                    concept_data = method(instance.uri)
                    instance.authority = manager.__name__
                    
                    logger.debug(
                        'Trying AuthorityManager {0}.'.format(manager.__name__))
                    
                    # Update description, label, (and typed).
                    instance.description = concept_data['description']

                    instance.label = concept_data[label_field]

                    # For Types, this will create a cascade of post_save
                    #  signals resulting in a crawl up the Type ontology
                    #  based on the ``supertype`` property.
                    if sender is Concept:
                        type_uri = concept_data['type_uri']
                    elif sender is Type:
                        try:
                            type_uri = concept_data['supertype_uri']
                        except KeyError:
                            type_uri = None

                    if type_uri is not None:
                        type_instance = Type.objects.get_or_create(
                                                    uri=type_uri)[0]
                        instance.typed = type_instance
                        logger.debug(
                            'Added Type {0} to Concept {1}.'.format(
                                            type_instance.uri, instance.uri))

                    instance.resolved = True
                    instance.save()
                    
                except Exception as E:
                    logger.error('Encountered Exception {0}.'.format(E))
                    continue

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