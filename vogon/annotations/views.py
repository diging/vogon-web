from itertools import chain

from rest_framework import viewsets, exceptions
from serializers import *
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from concepts.models import Concept
from concepts.authorities import search
from models import *

import hashlib

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class RepositoryViewSet(viewsets.ModelViewSet):
    queryset = Repository.objects.all()
    serializer_class = RepositorySerializer


class SessionViewSet(viewsets.ModelViewSet):
    queryset = Session.objects.all()
    serializer_class = SessionSerializer


class AppellationViewSet(viewsets.ModelViewSet):
    queryset = Appellation.objects.filter(asPredicate=False)
    serializer_class = AppellationSerializer

    def create(self, request):
        try:
            user = User.objects.get(pk=request.data.get('createdBy'))
        except ObjectDoesNotExist:
            raise exceptions.AuthenticationFailed('Fishy user data!')

        hashable = '|'.join([user.username, user.password])
        digest = hashlib.sha224(hashable).hexdigest()

        if request.data.get('userdigest') != digest:
            raise exceptions.AuthenticationFailed('Fishy user data!')
        return super(AppellationViewSet, self).create(request)

class PredicateViewSet(viewsets.ModelViewSet):
    queryset = Appellation.objects.filter(asPredicate=True)
    serializer_class = AppellationSerializer


class RelationViewSet(viewsets.ModelViewSet):
    queryset = Relation.objects.all()
    serializer_class = RelationSerializer


class TemporalBoundsViewSet(viewsets.ModelViewSet):
    queryset = TemporalBounds.objects.all()
    serializer_class = TemporalBoundsSerializer


class TextViewSet(viewsets.ModelViewSet):
    queryset = Text.objects.all()
    serializer_class = TextSerializer


class TypeViewSet(viewsets.ModelViewSet):
    queryset = Type.objects.all()
    serializer_class = TypeSerializer


class ConceptViewSet(viewsets.ModelViewSet):
    queryset = Concept.objects.all()
    serializer_class = ConceptSerializer

    def get_queryset(self, *args, **kwargs):
        queryset = super(ConceptViewSet, self).get_queryset(*args, **kwargs)

        # Limit results to those with ``pos``.
        pos = self.request.query_params.get('pos', None)
        if pos:
            if pos != 'all':
                queryset = queryset.filter(pos=pos)

        # Search Concept labels for ``search`` param.
        query = self.request.query_params.get('search', pos)
        if query:
            if pos == 'all':
                pos = None
            remote = [o.id for o in search(query, pos=pos)]
            queryset_remote = Concept.objects.filter(pk__in=remote)
            queryset = queryset.filter(label__contains=query) | queryset_remote

        return queryset


def annotate(request):
    return
