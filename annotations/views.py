from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.conf import settings
from django.core.serializers import serialize
from django.db.models import Q

from rest_framework import viewsets, exceptions, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from concepts.models import Concept
from concepts.authorities import search
from models import *
from forms import CrispyUserChangeForm
from serializers import *
from tasks import tokenize
from sources import EratosthenesManager

import hashlib
from itertools import chain
import requests
import re
from urlnorm import norm
from itertools import chain
import uuid

import json

sourceManager = EratosthenesManager(settings.ERATOSTHENES_ENDPOINT, settings.ERATOSTHENES_TOKEN)

def user_texts(user):
    return Text.objects.filter(relation__createdBy__pk=user.id).distinct()


def basepath(request):
    """
    Generate the base path (domain + path) for the site.
    """
    if request.is_secure():
        scheme = 'https://'
    else:
        scheme = 'http://'
    return scheme + request.get_host() + settings.SUBPATH


def user_recent_texts(user):
    by_relations = Text.objects.filter(relation__createdBy__pk=user.id)
    by_appellations = Text.objects.filter(appellation__createdBy__pk=user.id)
    result_list = list(set(chain(by_relations, by_appellations)))
    return result_list


def json_response(func):
    def decorator(request, *args, **kwargs):
        objects = func(request, *args, **kwargs)

        try:
            data = json.dumps(objects)
        except:
            if not hasattr(objects, '__iter__'):
                data = serialize("json", [objects])[1:-1]
            else:
                data = serialize("json", objects)
        return HttpResponse(data, "application/json")
    return decorator


@login_required
@json_response
def source_repositories(request):
    return sourceManager.repositories()


@login_required
@json_response
def source_repository(request, id):
    return sourceManager.repository(id)


@login_required
@json_response
def source_collections(request):
    return sourceManager.collections()


@login_required
@json_response
def source_collection(request, id):
    return sourceManager.collection(id)


@login_required
@json_response
def source_resources(request):
    return sourceManager.resources()


@login_required
@json_response
def source_resource(request, id):
    return sourceManager.resource(id)


@login_required
@json_response
def source_retrieve(request, uri):
    # TODO: Sanitize the URI?
    return sourceManager.retrieve(uri)


@login_required
@csrf_protect
def add_text(request):
    """
    Adds a remote Resource as a Text to a TextCollection.
    """

    if request.method == 'POST':
        """
        Retrieve text content from source.
        """

        data = json.loads(request.body)

        source, created = Repository.objects.get_or_create(name=data['source']['name'])
        text, created = Text.objects.get_or_create(
            uri = data['text']['uri'],
            defaults = {
                'title': data['text']['title'],
                'source': source,
                'addedBy': request.user,
            }
        )
        try:
            if created or len(text.tokenizedContent) == 0:
                cdata = tokenize(sourceManager.resourceContent(data['text']['uri']))
                text.tokenizedContent = cdata
        except Exception as E:
            print E
            raise E
        text.save()

        # Add to TextCollection.
        collection = TextCollection.objects.get(pk=data['addTo']['id'])
        collection.texts.add(text)
        collection.save()

        return HttpResponse(text.id)

@login_required
def user_settings(request):
    """ User profile settings"""

    if request.method == 'POST':
        form = CrispyUserChangeForm(request.POST)
        if form.is_valid():
            for field in ['first_name', 'last_name', 'email']:
                value = request.POST.get(field, None)
                if value:
                    setattr(request.user, field, value)
            request.user.save()
            return HttpResponseRedirect('/accounts/profile/')
    else:
        form = CrispyUserChangeForm(instance=request.user)

    template = loader.get_template('annotations/settings.html')
    context = RequestContext(request, {
        'user': request.user,
        'form': form,
        'subpath': settings.SUBPATH,
    })
    return HttpResponse(template.render(context))




@login_required
def dashboard(request):
    """
    Provides the user's personalized dashboard.
    """
    template = loader.get_template('annotations/dashboard.html')
    texts = user_recent_texts(request.user)
    context = RequestContext(request, {
        'user': request.user,
        'subpath': settings.SUBPATH,
        'baselocation': basepath(request),
        'texts': texts,
        'textCount': len(texts),
        'appellationCount': Appellation.objects.filter(createdBy__pk=request.user.id).filter(asPredicate=False).distinct().count(),
        'relationCount': Relation.objects.filter(createdBy__pk=request.user.id).distinct().count(),
    })
    return HttpResponse(template.render(context))


def network(request):
    """
    Provides a network browser view.
    """
    template = loader.get_template('annotations/network.html')
    context = {
        'baselocation': basepath(request),
        'user': request.user,
    }
    return HttpResponse(template.render(context))


@ensure_csrf_cookie
@login_required
def text(request, textid):
    """
    Provides the main text annotation view.
    """
    template = loader.get_template('annotations/text.html')
    text = get_object_or_404(Text, pk=textid)
    context = RequestContext(request, {
        'textid': textid,
        'text': text,
        'userid': request.user.id,
        'title': 'Annotate Text',
        'baselocation': basepath(request),
    })
    return HttpResponse(template.render(context))


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated, )


class RepositoryViewSet(viewsets.ModelViewSet):
    queryset = Repository.objects.all()
    serializer_class = RepositorySerializer
    permission_classes = (IsAuthenticated, )


class AppellationViewSet(viewsets.ModelViewSet):
    queryset = Appellation.objects.filter(asPredicate=False)
    serializer_class = AppellationSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self, *args, **kwargs):
        """
        """

        queryset = super(AppellationViewSet, self).get_queryset(*args, **kwargs)

        textid = self.request.query_params.get('text', None)
        userid = self.request.query_params.get('user', None)
        if textid:
            queryset = queryset.filter(occursIn=int(textid))
        if userid:
            queryset = queryset.filter(createdBy__pk=userid)
        else:
            queryset = queryset.filter(createdBy__pk=self.request.user.id)
        return queryset


class PredicateViewSet(viewsets.ModelViewSet):
    queryset = Appellation.objects.filter(asPredicate=True)
    serializer_class = AppellationSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self, *args, **kwargs):
        """
        """

        queryset = super(PredicateViewSet, self).get_queryset(*args, **kwargs)
        textid = self.request.query_params.get('text', None)
        userid = self.request.query_params.get('user', None)
        if textid:
            queryset = queryset.filter(occursIn=int(textid))
        if userid:
            queryset = queryset.filter(createdBy__pk=userid)
        else:
            queryset = queryset.filter(createdBy__pk=self.request.user.id)
        return queryset


class RelationViewSet(viewsets.ModelViewSet):
    queryset = Relation.objects.all()
    serializer_class = RelationSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self, *args, **kwargs):
        """
        """

        queryset = super(RelationViewSet, self).get_queryset(*args, **kwargs)

        textid = self.request.query_params.getlist('text')
        userid = self.request.query_params.getlist('user')
        typeid = self.request.query_params.getlist('type')
        conceptid = self.request.query_params.getlist('concept')
        # Refers to the predicate's interpretation, not the predicate itself.
        predicate_conceptid = self.request.query_params.getlist('predicate')

        if len(textid) > 0:
            queryset = queryset.filter(occursIn__in=[int(t) for t in textid])
        if len(typeid) > 0:
            queryset = queryset.filter(source__interpretation__typed__pk__in=[int(t) for t in typeid]).filter(object__interpretation__typed__pk__in=[int(t) for t in typeid])
        if len(predicate_conceptid) > 0:
            queryset = queryset.filter(predicate__interpretation__pk__in=[int(t) for t in predicate_conceptid])
        if len(conceptid) > 0:  # Source or target concept in `concept`.
            queryset = queryset.filter(Q(source__interpretation__id__in=[int(c) for c in conceptid]) | Q(object__interpretation__id__in=[int(c) for c in conceptid]))
        if len(userid) > 0:
            queryset = queryset.filter(createdBy__pk__in=[int(i) for i in userid])
        else:
            queryset = queryset.filter(createdBy__pk=self.request.user.id)

        return queryset


class TemporalBoundsViewSet(viewsets.ModelViewSet):
    queryset = TemporalBounds.objects.all()
    serializer_class = TemporalBoundsSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self, *args, **kwargs):
        """
        """

        queryset = super(TemporalBoundsViewSet, self).get_queryset(*args, **kwargs)
        textid = self.request.query_params.get('text', None)
        userid = self.request.query_params.get('user', None)
        if textid:
            queryset = queryset.filter(occursIn=int(textid))
        if userid:
            queryset = queryset.filter(createdBy__pk=userid)
        else:
            queryset = queryset.filter(createdBy__pk=self.request.user.id)
        return queryset


class TextViewSet(viewsets.ModelViewSet):
    queryset = Text.objects.all()
    serializer_class = TextSerializer
    permission_classes = (IsAuthenticated, )

    def get_queryset(self, *args, **kwargs):
        """
        A user can see only their own :class:`.TextCollection`\s.
        """

        queryset = super(TextViewSet, self).get_queryset(*args, **kwargs)

        textcollectionid = self.request.query_params.get('textcollection', None)
        conceptid = self.request.query_params.getlist('concept', None)
        if textcollectionid:
            queryset = queryset.filter(partOf=int(textcollectionid))
        if conceptid:
            queryset = queryset.filter(appellation__interpretation__pk__in=[int(c) for c in conceptid])

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
            queryset = queryset.filter(ownedBy__pk=self.userid)
        else:
            queryset = queryset.filter(ownedBy__pk=self.request.user.id)

        return queryset


    def create(self, request, *args, **kwargs):

        data = request.data
        if 'ownedBy' not in data:
            data['ownedBy'] = request.user.id
        print data

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)
        headers = self.get_success_headers(data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)




class TypeViewSet(viewsets.ModelViewSet):
    queryset = Type.objects.all()
    serializer_class = TypeSerializer
    permission_classes = (IsAuthenticated, )


class ConceptViewSet(viewsets.ModelViewSet):
    queryset = Concept.objects.all()
    serializer_class = ConceptSerializer
    permission_classes = (IsAuthenticated, )

    def create(self, request, *args, **kwargs):

        data = request.data
        if data['uri'] == 'generate':
            data['uri'] = 'http://vogon.asu.edu/{0}'.format(uuid.uuid4())
            data['resolved'] = True

        if 'lemma' not in data:
            data['lemma'] = data['label'].lower()


        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        self.perform_create(serializer)
        headers = self.get_success_headers(data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


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
