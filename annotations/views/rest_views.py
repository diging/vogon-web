"""
Provides all of the class-based views for the REST API.
"""

from django.db.models import Q
from django.conf import settings

from rest_framework import status
from rest_framework.settings import api_settings

from rest_framework import viewsets, exceptions, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework.pagination import (LimitOffsetPagination,
                                       PageNumberPagination)

from annotations.serializers import *
from annotations.tasks import get_manager
from annotations.models import (VogonUser, Repository, Appellation, RelationSet,
                                Relation, TemporalBounds, Text, TextCollection)
from concepts.models import Concept, Type
from concepts.tasks import search_concept

import uuid

import goat
goat.GOAT = settings.GOAT
goat.GOAT_APP_TOKEN = settings.GOAT_APP_TOKEN


# http://stackoverflow.com/questions/17769814/django-rest-framework-model-serializers-read-nested-write-flat
class SwappableSerializerMixin(object):
    def get_serializer_class(self):
        try:
            return self.serializer_classes[self.request.method]
        except AttributeError:
            logger.debug('%(cls)s does not have the required serializer_classes'
                         'property' % {'cls': self.__class__.__name__})
            raise AttributeError
        except KeyError:
            logger.debug('request method %(method)s is not listed'
                         ' in %(cls)s serializer_classes' %
                         {'cls': self.__class__.__name__,
                          'method': self.request.method})
            # required if you don't include all the methods (option, etc) in your serializer_class
            return super(SwappableSerializerMixin, self).get_serializer_class()


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


class AnnotationFilterMixin(object):
    """
    Mixin for :class:`viewsets.ModelViewSet` that provides filtering by
    :class:`.Text` and :class:`.User`\.
    """
    def get_queryset(self, *args, **kwargs):
        queryset = super(AnnotationFilterMixin, self).get_queryset(*args, **kwargs)

        textid = self.request.query_params.get('text', None)
        texturi = self.request.query_params.get('text_uri', None)
        userid = self.request.query_params.get('user', None)
        if textid:
            queryset = queryset.filter(occursIn=int(textid))
        if texturi:
            queryset = queryset.filter(occursIn__uri=texturi)
        if userid:
            queryset = queryset.filter(createdBy__pk=userid)
        elif userid is not None:
            queryset = queryset.filter(createdBy__pk=self.request.user.id)
        return queryset


class UserViewSet(viewsets.ModelViewSet):
    queryset = VogonUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )


class RepositoryViewSet(viewsets.ModelViewSet):
    queryset = Repository.objects.all()
    serializer_class = RepositorySerializer
    permission_classes = (IsAuthenticated, )


class RemoteCollectionViewSet(viewsets.ViewSet):
    def list(self, request, repository_pk=None):
        repository = Repository.objects.get(pk=repository_pk)
        manager = get_manager(repository.manager)(repository.endpoint)
        return Response(manager.collections())

    def retrieve(self, request, pk=None, repository_pk=None):
        repository = Repository.objects.get(pk=repository_pk)
        manager = get_manager(repository.manager)(repository.endpoint)
        return Response(manager.collection(pk))


class RemoteResourceViewSet(viewsets.ViewSet):
    def list(self, request, collection_pk=None, repository_pk=None):
        repository = Repository.objects.get(pk=repository_pk)
        manager = get_manager(repository.manager)(repository.endpoint)
        return Response(manager.collection(collection_pk))

    def retrieve(self, request, pk=None, collection_pk=None, repository_pk=None):
        repository = Repository.objects.get(pk=repository_pk)
        manager = get_manager(repository.manager)(repository.endpoint)
        return Response(manager.resource(pk))


class AppellationViewSet(SwappableSerializerMixin, AnnotationFilterMixin, viewsets.ModelViewSet):
    queryset = Appellation.objects.filter(asPredicate=False)
    serializer_class = AppellationSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )
    serializer_classes = {
        'GET': AppellationSerializer,
        'POST': AppellationPOSTSerializer
    }
    # pagination_class = LimitOffsetPagination

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        position = data.pop('position', None)
        interpretation = data.get('interpretation')

        # A concept URI may have been passed directly, in which case we need to
        #  get (or create) the local Concept instance.
        if type(interpretation) in [str, unicode] and interpretation.startswith('http'):
            try:
                concept = Concept.objects.get(uri=interpretation)
            except Concept.DoesNotExist:
                try:
                    concept_data = goat.Concept.retrieve(identifier=interpretation)
                    type_data = concept_data.data.get('concept_type')
                    type_instance = None
                    if type_data:
                        try:
                            type_instance = Type.objects.get(uri=type_data.get('identifier'))
                        except Type.DoesNotExist:
                            type_instance = Type.objects.create(
                                uri = type_data.get('identifier'),
                                label = type_data.get('name'),
                                description = type_data.get('description'),
                            )
                    concept = Concept.objects.create(
                        uri = interpretation,
                        label = concept_data.data.get('name'),
                        description = concept_data.data.get('description'),
                        typed = type_instance
                    )
                except Exception as E:
                    print E
                    raise E
            data['interpretation'] = concept.id

        # occursIn = data.pop('occursIn', None)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=data)
        # if occursIn:
        #     text = Text.objects.get(pk=occursIn)
        #     data
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as E:
            print E
            raise E

        # raise AttributeError('asdf')
        try:
            instance = serializer.save()
        except Exception as E:
            print ":::", E
            raise E

        # Prior to 0.5, the selected tokens were stored directly in Appellation,
        #  as ``tokenIds``. Now that we have several different annotation
        #  modes (e.g. images, HT/XML), we use the more flexible
        #  DocumentPosition model instead. For now, however, the JS app in the
        #  text annotation interface still relies on the original tokenId field.
        #  So until we modify that JS app, we still need to store tokenIds on
        #  Appellation, in addition to creating and linking a DocumentPosition.
        tokenIDs = serializer.data.get('tokenIds', None)

        text_id = serializer.data.get('occursIn')

        if tokenIDs:
            position = DocumentPosition.objects.create(
                        occursIn_id=text_id,
                        position_type=DocumentPosition.TOKEN_ID,
                        position_value=tokenIDs)

            instance.position = position
            instance.save()


        if position:
            if type(position) is not DocumentPosition:
                position_serializer = DocumentPositionSerializer(data=position)
                position_serializer.is_valid(raise_exception=True)
                position = position_serializer.save()

            instance.position = position
            instance.save()

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)



    def get_queryset(self, *args, **kwargs):

        queryset = AnnotationFilterMixin.get_queryset(self, *args, **kwargs)

        concept = self.request.query_params.get('concept', None)
        text = self.request.query_params.get('text', None)
        thisuser = self.request.query_params.get('thisuser', False)

        if thisuser:
            queryset = queryset.filter(createdBy_id=self.request.user.id)
        if concept:
            queryset = queryset.filter(interpretation_id=concept)
        if text:
            queryset = queryset.filter(occursIn_id=text)
        return queryset


class PredicateViewSet(AnnotationFilterMixin, viewsets.ModelViewSet):
    queryset = Appellation.objects.filter(asPredicate=True)
    serializer_class = AppellationSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )


class RelationSetViewSet(viewsets.ModelViewSet):
    queryset = RelationSet.objects.all()
    serializer_class = RelationSetSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )

    def get_queryset(self, *args, **kwargs):
        queryset = super(RelationSetViewSet, self).get_queryset(*args, **kwargs)

        textid = self.request.query_params.getlist('text')
        userid = self.request.query_params.getlist('user')

        if len(textid) > 0:
            queryset = queryset.filter(occursIn__in=[int(t) for t in textid])
        if len(userid) > 0:
            queryset = queryset.filter(createdBy__pk__in=[int(i) for i in userid])
        elif userid is not None and type(userid) is not list:
            queryset = queryset.filter(createdBy__pk=self.request.user.id)

        thisuser = self.request.query_params.get('thisuser', False)
        if thisuser:
            queryset = queryset.filter(createdBy_id=self.request.user.id)

        return queryset


class RelationViewSet(viewsets.ModelViewSet):
    queryset = Relation.objects.all()
    serializer_class = RelationSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )

    def get_queryset(self, *args, **kwargs):
        """
        Supports filtering by :class:`.Text`\, :class:`.User`\, node concept
        type, and predicate concept type.
        """

        queryset = super(RelationViewSet, self).get_queryset(*args, **kwargs)

        textid = self.request.query_params.getlist('text')
        userid = self.request.query_params.getlist('user')
        typeid = self.request.query_params.getlist('type')
        conceptid = self.request.query_params.getlist('concept')
        related_concepts = self.request.query_params.getlist('related_concepts')

        # Refers to the predicate's interpretation, not the predicate itself.
        predicate_conceptid = self.request.query_params.getlist('predicate')

        # TODO: clean this up.
        if len(textid) > 0:
            queryset = queryset.filter(occursIn__in=[int(t) for t in textid])
        if len(typeid) > 0:
            queryset = queryset.filter(source__interpretation__typed__pk__in=[int(t) for t in typeid]).filter(object__interpretation__typed__pk__in=[int(t) for t in typeid])
        if len(predicate_conceptid) > 0:
            queryset = queryset.filter(predicate__interpretation__pk__in=[int(t) for t in predicate_conceptid])
        if len(conceptid) > 0:  # Source or target concept in `concept`.
            queryset = queryset.filter(Q(source__interpretation__id__in=[int(c) for c in conceptid]) | Q(object__interpretation__id__in=[int(c) for c in conceptid]))
        if len(related_concepts) > 0:  # Source or target concept in `concept`.
            queryset = queryset.filter(Q(source__interpretation__id__in=[int(c) for c in related_concepts]) & Q(object__interpretation__id__in=[int(c) for c in related_concepts]))
        if len(userid) > 0:
            queryset = queryset.filter(createdBy__pk__in=[int(i) for i in userid])
        elif userid is not None and type(userid) is not list:
            queryset = queryset.filter(createdBy__pk=self.request.user.id)

        thisuser = self.request.query_params.get('thisuser', False)
        if thisuser:
            queryset = queryset.filter(createdBy_id=self.request.user.id)

        return queryset


# TODO: do we need this anymore?
class TemporalBoundsViewSet(viewsets.ModelViewSet, AnnotationFilterMixin):
    queryset = TemporalBounds.objects.all()
    serializer_class = TemporalBoundsSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )


class TextViewSet(viewsets.ModelViewSet):
    queryset = Text.objects.all()
    serializer_class = TextSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )
    # pagination_class = StandardResultsSetPagination

    def get_queryset(self, *args, **kwargs):
        """
        A user can see only their own :class:`.TextCollection`\s.
        """

        queryset = super(TextViewSet, self).get_queryset(*args, **kwargs)

        textcollectionid = self.request.query_params.get('textcollection', None)
        conceptid = self.request.query_params.getlist('concept')
        related_concepts = self.request.query_params.getlist('related_concepts')
        uri = self.request.query_params.get('uri', None)

        if textcollectionid:
            queryset = queryset.filter(partOf=int(textcollectionid))
        if uri:
            queryset = queryset.filter(uri=uri)
        if len(conceptid) > 0:
            queryset = queryset.filter(appellation__interpretation__pk__in=[int(c) for c in conceptid])
        if len(related_concepts) > 1:
            queryset = queryset.filter(appellation__interpretation_id=int(related_concepts[0])).filter(appellation__interpretation_id=int(related_concepts[1]))

        return queryset.distinct()


class TextCollectionViewSet(viewsets.ModelViewSet):
    queryset = TextCollection.objects.all()
    serializer_class = TextCollectionSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self, *args, **kwargs):
        """
        """
        queryset = super(TextCollectionViewSet, self).get_queryset(*args, **kwargs)

        userid = self.request.query_params.get('user', None)
        if userid:
            queryset = queryset.filter(ownedBy__pk=userid)
        else:
            queryset = queryset.filter(Q(ownedBy__pk=self.request.user.id) | Q(participants=self.request.user.id))
        return queryset

    def create(self, request, *args, **kwargs):

        data = request.data
        if 'ownedBy' not in data:
            data['ownedBy'] = request.user.id
        if 'participants' not in data:
            data['participants'] = []

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)
        headers = self.get_success_headers(data)

        return Response(serializer.data,
                        status=status.HTTP_201_CREATED,
                        headers=headers)


class TypeViewSet(viewsets.ModelViewSet):
    queryset = Type.objects.all()
    serializer_class = TypeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )


class ConceptViewSet(viewsets.ModelViewSet):
    queryset = Concept.objects.filter(~Q(concept_state=Concept.REJECTED))
    serializer_class = ConceptSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )

    def create(self, request, *args, **kwargs):
        print "ConceptViewSet:: create::", request.data
        data = request.data
        if data['uri'] == 'generate':
            data['uri'] = 'http://vogonweb.net/{0}'.format(uuid.uuid4())

        if 'lemma' not in data:
            data['lemma'] = data['label'].lower()

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)
        headers = self.get_success_headers(data)
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED,
                        headers=headers)

    @list_route()
    def search(self, request, **kwargs):
        q = request.GET.get('search', None)
        pos = request.GET.get('pos', None)

        concepts = goat.Concept.search(q=q, pos=pos)
        def _relabel(datum):
            _fields = {
                'name': 'label',
                'id': 'alt_id',
                'identifier': 'uri'
            }
            return {_fields.get(k, k): v for k, v in datum.iteritems()}
        return Response({'results': map(_relabel, [c.data for c in concepts])})


    def get_queryset(self, *args, **kwargs):
        """
        Filter by part of speach (``pos``).
        """
        queryset = super(ConceptViewSet, self).get_queryset(*args, **kwargs)

        # Limit results to those with ``pos``.
        pos = self.request.query_params.get('pos', None)
        if pos:
            if pos != 'all':
                queryset = queryset.filter(pos__in=[pos.upper(), pos.lower()])

        # Search Concept labels for ``search`` param.
        query = self.request.query_params.get('search', None)
        remote = self.request.query_params.get('remote', False)
        uri = self.request.query_params.get('uri', None)
        type_id = self.request.query_params.get('typed', None)
        type_strict = self.request.query_params.get('strict', None)
        type_uri = self.request.query_params.get('type_uri', None)
        max_results = self.request.query_params.get('max', None)

        if uri:
            queryset = queryset.filter(uri=uri)
        if type_uri:
            queryset = queryset.filter(type__uri=uri)
        if type_id:
            if type_strict:
                queryset = queryset.filter(typed_id=type_id)
            else:
                queryset = queryset.filter(Q(typed_id=type_id) | Q(typed=None))
        if query:
            if pos == 'all':
                pos = None

            # if remote:  # Spawn asynchronous calls to authority services.
            #     search_concept.delay(query, pos=pos)
            queryset = queryset.filter(label__icontains=query)

        if max_results:
            return queryset[:max_results]
        return queryset


def concept_search(request):
    q = request.get('search', None)
    pos = self.request.query_params.get('pos', None)
    return goat.Concept.search(q=q, pos=pos)
