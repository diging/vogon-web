from rest_framework import viewsets
from serializers import *
from django.contrib.auth.models import User
from concepts.models import Concept
from models import *


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
    queryset = Appellation.objects.all()
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


class ConceptViewSet(viewsets.ModelViewSet):
    queryset = Concept.objects.all()
    serializer_class = ConceptSerializer

    def get_queryset(self, *args, **kwargs):
        queryset = super(ConceptViewSet, self).get_queryset(*args, **kwargs)
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(label__contains=search)
        return queryset


def annotate(request):
    return