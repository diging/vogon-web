from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.template import RequestContext, loader
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.conf import settings
from django.core.serializers import serialize
from django.db.models import Q
from django.utils.safestring import mark_safe
from django.core.files import File
from guardian.shortcuts import get_objects_for_user

from rest_framework import viewsets, exceptions, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination

from concepts.models import Concept
from concepts.authorities import search
from concepts.tasks import search_concept

from models import *
from forms import CrispyUserChangeForm, UploadFileForm
from serializers import *
from tasks import *

import hashlib
from itertools import chain
import requests
import re
from urlnorm import norm
from itertools import chain
import uuid

import json


def home(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('dashboard'))
    return HttpResponseRedirect(reverse('django.contrib.auth.views.login'))


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


@login_required
def list_texts(request):
    """
    List all of the texts that the user can see, with links to annotate them.
    """
    template = loader.get_template('annotations/list_texts.html')

    text_list = get_objects_for_user(request.user, 'annotations.view_text')

    # text_list = Text.objects.all()
    paginator = Paginator(text_list, 25)

    page = request.GET.get('page')
    try:
        texts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        texts = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        texts = paginator.page(paginator.num_pages)

    context = {
        'texts': texts,
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

    # If a text is restricted, then the user needs explicit permission to
    #  access it.
    if not text.public and not request.user.has_perm('annotations.view_text'):
        # TODO: return a pretty templated response.
        return HttpResponseForbidden("Sorry, this text is restricted.")

    context = RequestContext(request, {
        'textid': textid,
        'text': text,
        'userid': request.user.id,
        'title': 'Annotate Text',
        'baselocation': basepath(request),
    })
    return HttpResponse(template.render(context))


### REST API class-based views.


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
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


class AnnotationFilterMixin(object):
    """
    Mixin for :class:`viewsets.ModelViewSet` that provides filtering by
    :class:`.Text` and :class:`.User`\.
    """
    def get_queryset(self, *args, **kwargs):
        queryset = super(AnnotationFilterMixin, self).get_queryset(*args, **kwargs)

        textid = self.request.query_params.get('text', None)
        userid = self.request.query_params.get('user', None)
        if textid:
            queryset = queryset.filter(occursIn=int(textid))
        if userid:
            queryset = queryset.filter(createdBy__pk=userid)
        elif userid is not None:
            queryset = queryset.filter(createdBy__pk=self.request.user.id)
        return queryset


class AppellationViewSet(AnnotationFilterMixin, viewsets.ModelViewSet):
    queryset = Appellation.objects.filter(asPredicate=False)
    serializer_class = AppellationSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )


class PredicateViewSet(AnnotationFilterMixin, viewsets.ModelViewSet):
    queryset = Appellation.objects.filter(asPredicate=True)
    serializer_class = AppellationSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )


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
        if len(userid) > 0:
            queryset = queryset.filter(createdBy__pk__in=[int(i) for i in userid])
        elif userid is not None and type(userid) is not list:
            queryset = queryset.filter(createdBy__pk=self.request.user.id)

        return queryset


class TemporalBoundsViewSet(viewsets.ModelViewSet, AnnotationFilterMixin):
    queryset = TemporalBounds.objects.all()
    serializer_class = TemporalBoundsSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000


class TextViewSet(viewsets.ModelViewSet):
    queryset = Text.objects.all()
    serializer_class = TextSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )
    pagination_class = StandardResultsSetPagination

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
    queryset = Concept.objects.all()
    serializer_class = ConceptSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )

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
        if query:
            if pos == 'all':
                pos = None

            if remote:  # Spawn asynchronous calls to authority services.
                search_concept.delay(query, pos=pos)
            # remote = [o.id for o in search(query, pos=pos)]
            # queryset_remote = Concept.objects.filter(pk__in=remote)
            queryset = queryset.filter(label__contains=query)# | queryset_remote

        return queryset

@login_required
def upload_file(request):
    """
    Upload a file and save the text instance.

    Parameters
    ----------
    request : HTTPRequest
        The request after submitting file upload form
    """
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                handle_file_upload(request, form)
                return HttpResponseRedirect(reverse('list_texts'))
            except Exception as detail:
                print detail
                form = UploadFileForm()
    else:
        form = UploadFileForm()

    template = loader.get_template('annotations/upload_file.html')
    context = RequestContext(request, {
        'user': request.user,
        'form': form,
        'subpath': settings.SUBPATH,
    })
    return HttpResponse(template.render(context))

def handle_file_upload(request, form):
    """
    Handle the uploaded file and route it to corresponding handlers

    Parameters
    ----------
    request : HTTPRequest
        The request after submitting file upload form
    form : Form
        The form with uploaded content
    """
    uploaded_file = request.FILES['filetoupload']
    text_title = form.cleaned_data['title']
    date_created = form.cleaned_data['datecreated']
    is_public = form.cleaned_data['ispublic']
    user = request.user
    if uploaded_file.content_type == 'text/plain':
        file_content = extract_text_file(uploaded_file)
        tokenized_content = tokenize(file_content)
        save_text_instance(tokenized_content, text_title, date_created, is_public, user)
    elif uploaded_file.content_type == 'application/pdf':
        extract_pdf_file(uploaded_file)
