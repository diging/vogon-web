# TODO: we really should refactor this to rely on Goat.


from .models import Concept, Type

from conceptpower import Conceptpower
from urllib.parse import urlparse
from django.conf import settings

import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')


class AuthorityManager(object):
    pass


class ConceptpowerAuthority(AuthorityManager, Conceptpower):
    __name__ = 'Conceptpower'

    endpoint = settings.CONCEPTPOWER_ENDPOINT
    namespace = settings.CONCEPTPOWER_NAMESPACE

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
        r['label'] = r['word']
        instance, created = Concept.objects.get_or_create(
                                uri=r['uri'],
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

    if instance is None:
        return

    try:    # Configure based on sender model class.
        instance_cast = instance.cast()
    except Exception as E:
        return

    if type(instance_cast) is Concept:
        get_method = 'get'
        label_field = 'word'
    elif type(instance_cast) is Type:
        get_method = 'get_type'
        label_field = 'type'

    # Skip any instance that has already been resolved, or that lacks a URI.
    if not (instance.resolved or instance.concept_state == Concept.RESOLVED) and instance.uri is not None:
        logger.debug('Instance {0} not yet resolved.'.format(instance.id))

        manager_class = ConceptpowerAuthority
        if manager_class.namespace == get_namespace(instance.uri):
            manager = manager_class()
            method = getattr(manager, get_method)
            concept_data = method(instance.uri)
            concept_data['label'] = concept_data.get(label_field, 'No label')
            instance.authority = manager.__name__

            logger.debug(
                'Trying AuthorityManager {0}.'.format(manager.__name__))

            instance.resolved = True
            instance.concept_state = Concept.RESOLVED
            update_instance(sender, instance, concept_data, manager.__name__)
            instance.refresh_from_db()
            return instance


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


def add(instance):
    """
    Add the approved concept to Conceptpower

    Parameters
    -----------
    instance : :class:'.Concept'

    Returns
    -------
    response : dict

    Examples
    -------

    .. code-block:: python

       >>> add(concept)
       {
           u'word': u'Askania-Nova',
           u'description': u'A biosphere reserve located in Kherson Oblast, Ukraine',
           u'conceptlist': u'VogonWeb Concepts',
           u'type': u'http://www.digitalhps.org/types/TYPE_dfc95f97-f128-42ae-b54c-ee40333eae8c',
           u'equals': [],
           u'pos': u'noun',
           u'synonymids': [],
           u'similar': [],
           u'id': u'CONf3a936bd-f9fe-415c-8e9e-e463de7d4bbf'
       }
    """

    concept_list = 'VogonWeb Concepts'
    conceptpower = ConceptpowerAuthority()

    if not instance.typed:
        raise RuntimeError('Cannot add a concept without a type')

    pos = instance.pos
    if not pos:
        pos = 'noun'
    kwargs = {}
    if instance.uri:
        kwargs.update({
            'equal_uris': instance.uri
        })
    response = conceptpower.create(settings.CONCEPTPOWER_USERID,
                                   settings.CONCEPTPOWER_PASSWORD,
                                   instance.label, pos.lower(),
                                   concept_list, instance.description,
                                   instance.typed.uri)

    # This is kind of hacky, but the current version of Conceptpower does not
    #  return the full URI of the new Concept -- just its ID. We can remove this
    #  when the new version of Conceptpower is released.
    if 'uri' not in response:
        response['uri'] = 'http://www.digitalhps.org/concepts/%s' % response['id']
    return response
