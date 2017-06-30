from django.conf import settings

from urlparse import urlparse
from conceptpower import Conceptpower

from concepts.models import *

TYPES = {
    'viaf:personal': "986a7cc9-c0c1-4720-b344-853f08c136ab",    # E21 Person
    'viaf:corporate': "3fc436d0-26e7-472c-94de-0b712b66b3f3",   # E40 Legal Body
    'viaf:geographic': "dfc95f97-f128-42ae-b54c-ee40333eae8c"    # E53 Place
}


class ConceptLifecycleException(Exception):
    pass


class ConceptUpstreamException(Exception):
    pass


class ConceptData(object):
    """
    Container for raw data from Conceptpower.
    """
    def __init__(self, label=None, description=None, typed=None, uri=None,
                 pos='noun', equal_to=[]):
        self.label = label
        self.description = description
        self.typed = typed
        self.uri = uri
        self.pos=pos
        self.equal_to = equal_to


class ConceptLifecycle(object):
    """
    Shepherds :class:`.Concept` instances through their life cycle in VW.
    """

    CONCEPTPOWER = 'http://www.digitalhps.org/'
    VOGONWEB = 'http://vogonweb.net/'
    DEFAULT_TYPE = 'c7d0bec3-ea90-4cde-8698-3bb08c47d4f2'   # E1 Entity.
    DEFAULT_LIST = "Vogon"    # This seems kind of unneecessary, but oh well.

    def __init__(self, instance):
        assert isinstance(instance, Concept)
        self.instance = instance
        self.conceptpower = Conceptpower()

        self.conceptpower.endpoint = settings.CONCEPTPOWER_ENDPOINT
        self.conceptpower.namespace = settings.CONCEPTPOWER_NAMESPACE
        self.user = settings.CONCEPTPOWER_USERID
        self.password = settings.CONCEPTPOWER_PASSWORD

    @staticmethod
    def get_namespace(uri):
        """
        Extract namespace from URI.
        """

        o = urlparse(uri)
        namespace = o.scheme + "://" + o.netloc + "/"

        if o.scheme == '' or o.netloc == '':
            return None
            # raise ConceptLifecycleException("Could not determine namespace for %s." % uri)

        return namespace

    def _get_namespace(self):
        return ConceptLifecycle.get_namespace(self.instance.uri)

    @property
    def is_native(self):
        """
        A native concept is one that exists in the Conceptpower namespace.
        """
        return self._get_namespace() == self.CONCEPTPOWER

    @property
    def is_created(self):
        return self._get_namespace() == self.VOGONWEB

    @property
    def is_external(self):
        print self._get_namespace(), self.is_native, self.is_created
        return not (self.is_native or self.is_created)

    @property
    def default_state(self):
        """
        The state that a :class:`.Concept` should adopt upon instantiation
        depends on whether it is native, created, or external.
        """
        if self.is_native:
            return Concept.RESOLVED
        elif self.is_created:
            return Concept.PENDING
        elif self.is_external:
            return Concept.APPROVED
        elif self.instance.uri:
            return Concept.APPROVED

    @staticmethod
    def create(**params):
        """
        Create a new :class:`.Concept` instance, and return its
        :class:`.ConceptLifecycle` manager.
        """
        resolve = params.pop('resolve', True)
        if 'pos' not in params:
            params['pos'] = 'noun'
        manager = ConceptLifecycle(Concept(**params))
        manager.instance.concept_state = manager.default_state
        manager.instance.save()
        return manager

    @staticmethod
    def get_or_create(**params):
        try:
            return Concept.objects.get(uri=params.get('uri'))
        except Concept.DoesNotExist:
            return ConceptLifecycle.create(**params)

    @staticmethod
    def create_from_raw(data):
        _type_uri = data.get('type_uri')
        if _type_uri:
            _typed, _ = Type.objects.get_or_create(uri=_type_uri)
        else:
            _typed = None

        manager = ConceptLifecycle.create(
            uri = data.get('uri') if data.get('uri') else data.get('id'),
            label = data.get('word') if data.get('word') else data.get('lemma'),
            description = data.get('description'),
            pos = data.get('pos'),
            typed = _typed,
            authority = 'Conceptpower',
        )
        return manager

    def approve(self):
        if self.instance.concept_state == Concept.RESOLVED:
            raise ConceptLifecycleException("This concept is already resolved.")
        if self.instance.concept_state == Concept.MERGED:
            raise ConceptLifecycleException("This concept is merged, and cannot"
                                            " be approved.")

        self.instance.concept_state = Concept.APPROVED
        self.instance.save()

    def resolve(self):
        """

        """
        if self.instance.concept_state == Concept.RESOLVED:
            raise ConceptLifecycleException("This concept is already resolved")
        if self.instance.concept_state == Concept.MERGED:
            raise ConceptLifecycleException("This concept is merged, and cannot"
                                            " be resolved")
        if self.is_created:
            raise ConceptLifecycleException("Created concepts cannot be"
                                            " resolved")

        if self.is_native:
            data = self.get(self.instance.uri)
            if data.typed:
                _typed, _ = Type.objects.get_or_create(uri=data.typed)
            else:
                _typed = None

            self.instance.label = data.label
            self.instance.description = data.description
            if _typed:
                self.instance.typed = _typed
            self.instance.pos = data.pos
            self.instance.concept_state = Concept.RESOLVED
            self.instance.save()
            return

        if self.is_external:
            matching = self.get_matching()
            if matching:
                if len(matching) > 1:
                    raise ConceptLifecycleException("There are more than one"
                                                    " matching native concepts"
                                                    " for this external"
                                                    " concept.")
                match = matching.pop()
                self.merge_with(match.uri)

            if self.get_similar():
                raise ConceptLifecycleException("Cannot resolve an external"
                                                " concept with similar native"
                                                " entries in Conceptpower.")

            # External concepts with no matching or similar concepts in
            #  Conceptpower can be added automatically.
            self.add()
            return
        raise ConceptLifecycleException("Could not resolve concept.")


    def merge_with(self, uri):
        """
        Merge the managed :class:`.Concept` with some other concept.
        """
        if self.is_native:
            raise ConceptLifecycleException("Cannot merge a native concept")

        # We use the boilerplate try..except here to avoid making unneecessary
        #  API calls.
        try:
            target = Concept.objects.get(uri=uri)
        except Concept.DoesNotExist:
            try:
                data = self.conceptpower.get(uri)
            except Exception as E:
                raise ConceptUpstreamException("Whoops: %s" % str(E))
            target = ConceptLifecycle.create_from_raw(data).instance

        self.instance.merged_with = target
        self.instance.concept_state = Concept.MERGED
        self.instance.save()

        # It may be the case that other concepts have been merged into these
        #  unresolved concepts. Therefore, we recursively collect all of
        #  these "child" concepts, and point them to the master concept.
        children_queryset = Concept.objects.filter(pk__in=self.instance.children)
        children_queryset.update(merged_with=target)

    def add(self):
        """
        Use data from the managed :class:`.Concept` instance to create a new
        native entry in Conceptpower.
        """
        if self.is_native:
            raise ConceptLifecycleException("This concept already exists in"
                                            " Conceptpower, genius!")

        # If the managed Concept is external (e.g. from VIAF), we want to be
        #  sure to reference it in the new Conceptpower entry so that other
        #  users can benefit. Ideally this would happen with BlackGoat
        #  identities, but we have some  use-cases that depend on the
        #  equal_to field in Conceptpower.
        equal_uris = []
        if self.is_external:
            equal_uris.append(self.instance.uri)

        # It is possible that the managed Concept does not have a type, and
        #  sometimes we just don't care.
        concept_type = getattr(self.instance.typed, 'uri', self.DEFAULT_TYPE)
        if ConceptLifecycle.get_namespace(concept_type) != ConceptLifecycle.CONCEPTPOWER:
            concept_type = TYPES.get(concept_type)
        if not concept_type:
            raise ConceptLifecycleException("Cannot create a new concept"
                                            " without a valid Conceptpower"
                                            " type id.")

        pos = self.instance.pos
        if not pos:
            pos = 'noun'
        try:
            data = self.conceptpower.create(self.user, self.password,
                                            self.instance.label, pos,
                                            self.DEFAULT_LIST,
                                            self.instance.description,
                                            concept_type,
                                            equal_uris=equal_uris)
        except Exception as E:
            raise ConceptUpstreamException("There was an error adding the"
                                           " concept to Conceptpower:"
                                           " %s" % str(E))
        target = ConceptLifecycle.create_from_raw(data).instance
        self.instance.merged_with = target
        self.instance.concept_state = Concept.MERGED
        self.instance.save()

    def _reform(self, raw):
        return ConceptData(**{
            'label': raw.get('word') if raw.get('word') else raw.get('lemma'),
            'uri': raw.get('uri') if raw.get('uri') else raw.get('id'),
            'description': raw.get('description'),
            'typed': raw.get('type_uri'),
            'equal_to': raw.get('equal_to', []),
            'pos': raw.get('pos'),
        })

    def get(self, uri):
        try:
            raw = self.conceptpower.get(uri)
        except Exception as E:
            raise ConceptUpstreamException("Whoops: %s" % str(E))
        return self._reform(raw)

    def get_similar(self):
        """
        Retrieve data about similar entries in Conceptpower.

        Returns
        -------
        list
            A list of dicts with raw data from Conceptpower.
        """
        import re, string
        from unidecode import unidecode

        q = re.sub("[0-9]", "", unidecode(self.instance.label).translate(None, string.punctuation).lower())
        if not q:
            return []
        try:
            data = self.conceptpower.search(q)
        except Exception as E:
            raise ConceptUpstreamException("Whoops: %s" % str(E))
        return map(self._reform, data)

    def get_matching(self):
        """
        Retrieve data about Conceptpower entries that are "equal to" the
        managed :class:`.Concept`\.

        Returns
        -------
        list
            A list of dicts with raw data from Conceptpower.
        """
        try:
            data = self.conceptpower.search(equal_to=self.instance.uri)
        except Exception as E:
            raise ConceptUpstreamException("Whoops: %s" % str(E))
        return map(self._reform, data)
