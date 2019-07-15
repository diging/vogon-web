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
from rest_framework.decorators import action
from rest_framework.pagination import (LimitOffsetPagination,
                                       PageNumberPagination)

from annotations.serializers import *
from annotations.models import *
from concepts.models import Concept, Type
from concepts.lifecycle import *

import uuid

import goat
goat.GOAT = settings.GOAT
goat.GOAT_APP_TOKEN = settings.GOAT_APP_TOKEN

import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(settings.LOGLEVEL)



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
        position_type = self.request.query_params.get('position_type', None)
        if position_type:
            queryset = queryset.filter(position__position_type=position_type )
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


class DateAppellationViewSet(AnnotationFilterMixin, viewsets.ModelViewSet):
    queryset = DateAppellation.objects.all()
    serializer_class = DateAppellationSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )

    def create(self, request, *args, **kwargs):
        print((request.data))
        data = request.data.copy()
        position = data.pop('position', None)
        if 'month' in data and data['month'] is None:
            data.pop('month')
        if 'day' in data and data['day'] is None:
            data.pop('day')
        serializer_class = self.get_serializer_class()

        try:
            serializer = serializer_class(data=data)
        except Exception as E:
            print((serializer.errors))
            raise E

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as E:
            print((serializer.errors))
            raise E

        # raise AttributeError('asdf')
        try:
            instance = serializer.save()
        except Exception as E:
            print((":::", E))
            raise E

        text_id = serializer.data.get('occursIn')

        if position:
            if type(position) is not DocumentPosition:
                position_serializer = DocumentPositionSerializer(data=position)
                try:
                    position_serializer.is_valid(raise_exception=True)
                except Exception as E:
                    print(("DocumentPosition::", position_serializer.errors))
                    raise E
                position = position_serializer.save()

            instance.position = position
            instance.save()

        instance.refresh_from_db()
        reserializer = DateAppellationSerializer(instance, context={'request': request})

        headers = self.get_success_headers(serializer.data)
        return Response(reserializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)



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
        if type(interpretation) in [str, str] and interpretation.startswith('http'):
            try:
                concept = Concept.objects.get(uri=interpretation)
            except Concept.DoesNotExist:

                concept_data = goat.Concept.retrieve(identifier=interpretation)
                type_data = concept_data.data.get('concept_type')
                type_instance = None
                if type_data:
                    try:
                        type_instance = Type.objects.get(uri=type_data.get('identifier'))
                    except Type.DoesNotExist:
                        print(type_data)
                        type_instance = Type.objects.create(
                            uri = type_data.get('identifier'),
                            label = type_data.get('name'),
                            description = type_data.get('description'),
                            authority = concept_data.data.get('authority', {}).get('name'),
                        )

                concept = ConceptLifecycle.create(
                    uri = interpretation,
                    label = concept_data.data.get('name'),
                    description = concept_data.data.get('description'),
                    typed = type_instance,
                    authority = concept_data.data.get('authority', {}).get('name'),
                ).instance

            data['interpretation'] = concept.id

        serializer_class = self.get_serializer_class()

        try:
            serializer = serializer_class(data=data)
        except Exception as E:
            print((serializer.errors))
            raise E

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as E:
            print((serializer.errors))
            raise E

        # raise AttributeError('asdf')
        try:
            instance = serializer.save()
        except Exception as E:
            print((":::", E))
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
                try:
                    position_serializer.is_valid(raise_exception=True)
                except Exception as E:
                    print(("DocumentPosition::", position_serializer.errors))
                    raise E
                position = position_serializer.save()

            instance.position = position
            instance.save()

        instance.refresh_from_db()
        reserializer = AppellationSerializer(instance, context={'request': request})

        headers = self.get_success_headers(serializer.data)
        return Response(reserializer.data, status=status.HTTP_201_CREATED,
                        headers=headers)

    # TODO: implement some real filters!
    def get_queryset(self, *args, **kwargs):

        queryset = AnnotationFilterMixin.get_queryset(self, *args, **kwargs)

        concept = self.request.query_params.get('concept', None)
        text = self.request.query_params.get('text', None)
        thisuser = self.request.query_params.get('thisuser', False)
        project_id = self.request.query_params.get('project', None)
        position_type = self.request.query_params.get('position_type', None)
        if thisuser:
            queryset = queryset.filter(createdBy_id=self.request.user.id)
        if concept:
            queryset = queryset.filter(interpretation_id=concept)
        if text:
            queryset = queryset.filter(occursIn_id=text)
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        if position_type and position_type in DocumentPosition.TYPES:
            queryset = queryset.filter(position__position_type=position_type)
        return queryset.order_by('-created')


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
        project_id = self.request.query_params.get('project', None)
        if thisuser:
            queryset = queryset.filter(createdBy_id=self.request.user.id)
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        return queryset.order_by('-created')


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
        print(("ConceptViewSet:: create::", request.data))
        data = request.data
        if data['uri'] == 'generate':
            data['uri'] = 'http://vogonweb.net/{0}'.format(uuid.uuid4())

        if 'lemma' not in data:
            data['lemma'] = data['label']

        concept_type = data.get('typed', '')
        try:
            int(concept_type)
        except:
            data['typed'] = Type.objects.get(uri=concept_type).id

        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as E:
            print((serializer.errors))
            raise E

        self.perform_create(serializer)
        headers = self.get_success_headers(data)
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED,
                        headers=headers)

    @action(detail=False)
    def search(self, request, **kwargs):
        q = request.GET.get('search', None)
        if not q:
            return Response({'results': []})
        pos = request.GET.get('pos', None)
        concepts = goat.Concept.search(q=q, pos=pos, limit=50)

        def _relabel(datum):
            _fields = {
                'name': 'label',
                'id': 'alt_id',
                'identifier': 'uri'
            }

            return {_fields.get(k, k): v for k, v in list(datum.items())}
        return Response({'results': list(map(_relabel, [c.data for c in concepts]))})


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

            queryset = queryset.filter(label__icontains=query)

        if max_results:
            return queryset[:max_results]
        return queryset


def concept_search(request):
    q = request.get('search', None)
    pos = self.request.query_params.get('pos', None)
    return goat.Concept.search(q=q, pos=pos)
