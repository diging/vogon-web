from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.template import RequestContext, loader
from annotations.models import VogonUser
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login,authenticate
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.conf import settings
from django.core.serializers import serialize
from django.db.models import Q, Count
from django.utils.safestring import mark_safe
from django.core.files import File
from guardian.shortcuts import get_objects_for_user, get_perms
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.response import Response
from rest_framework.settings import api_settings

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
from forms import *
from serializers import *
from tasks import *

import hashlib
from itertools import chain
from collections import OrderedDict
import requests
import re
from urlnorm import norm
from itertools import chain
import uuid
import igraph

import json

from django.shortcuts import render

import logging
logger = logging.getLogger(__name__)

from haystack.generic_views import SearchView
from haystack.query import SearchQuerySet


def home(request):
    """

    Provides a landing page containing information about the application
    for user who are not authenticated

    LoggedIn users are redirected to the dashboard view
    ----------
    request : HTTPRequest
        The request for application landing page.
    Returns
    ----------
    :template:
        Renders landing page for non-loggedin user and
        dashboard view for loggedin users.
    """
    template = loader.get_template('registration/home.html')
    user_count = VogonUser.objects.filter(is_active=True).count()
    text_count = Text.objects.all().count()
    relation_count = Relation.objects.count()
    context = RequestContext(request, {
        'user_count': user_count,
        'text_count': text_count,
        'relation_count': relation_count
    })
    return HttpResponse(template.render(context))


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

@csrf_protect
def register(request):
    """
    Provide registration view and stores a user on receiving user detail from registration form.
    Parameters
    ----------
    request : HTTPRequest
        The request after submitting registration form.
    Returns
    ----------
    :template:
        Renders registration form for get request. Redirects to dashboard
        for post request.
    """
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = VogonUser.objects.create_user(
            form.cleaned_data['username'],
            form.cleaned_data['email'],
            password=form.cleaned_data['password1'],
            full_name=form.cleaned_data['full_name'],
            affiliation=form.cleaned_data['affiliation'],
            location=form.cleaned_data['location'],
            )

            g = Group.objects.get_or_create(name='Public')[0]
            user.groups.add(g)
            user.save()
            new_user = authenticate(username=form.cleaned_data['username'],
                                    password=form.cleaned_data['password1'])
            # Logs in new user
            login(request, new_user)
            return HttpResponseRedirect(reverse('dashboard'))
    else:
        form = RegistrationForm()
    variables = RequestContext(request, {
    'form': form
    })

    return render(request,
    'registration/register.html',
    {'form': form},
    )

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
        form = UserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/accounts/profile/')
    else:
        form = UserChangeForm(instance=request.user)

    template = loader.get_template('annotations/settings.html')
    context = RequestContext(request, {
        'user': request.user,
        'form': form,
        'subpath': settings.SUBPATH,
    })
    return HttpResponse(template.render(context))

def about(request):
    """
    Provides information about Vogon-Web
    """
    template = loader.get_template('annotations/about.html')
    context = RequestContext(request)
    return HttpResponse(template.render(context))

@login_required
def dashboard(request):
    """
    Provides the user's personalized dashboard.
    """

    template = loader.get_template('annotations/dashboard.html')
    texts = user_recent_texts(request.user)
    baselocation = basepath(request)
    if baselocation[-1] == '/':
        baselocation = baselocation[:-1]
    context = RequestContext(request, {
        'user': request.user,
        'subpath': settings.SUBPATH,
        'baselocation': baselocation,
        'texts': texts,
        'textCount': len(texts),
        'appellationCount': Appellation.objects.filter(createdBy__pk=request.user.id).filter(asPredicate=False).distinct().count(),
        'relation_count': Relation.objects.filter(createdBy__pk=request.user.id).distinct().count(),
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


def list_texts(request):
    """
    List all of the texts that the user can see, with links to annotate them.
    """
    template = loader.get_template('annotations/list_texts.html')

    text_list = get_objects_for_user(request.user, 'annotations.view_text')

    order_by = request.GET.get('order_by', 'title')
    text_list = text_list.order_by(order_by)

    paginator = Paginator(text_list, 15)

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
        'order_by': order_by,
        'user': request.user,
    }
    return HttpResponse(template.render(context))


def list_user(request):
    """
    List all the users of Vogon web
    """

    template = loader.get_template('annotations/contributors.html')

    search_term = request.GET.get('search_term')
    sort = request.GET.get('sort', 'username')
    queryset = VogonUser.objects.exclude(id = -1).order_by(sort)

    if search_term:
        queryset = queryset.filter(full_name__icontains = search_term)

    paginator = Paginator(queryset, 10)

    page = request.GET.get('page')
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        users = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        users = paginator.page(paginator.num_pages)

    context = {
        'search_term' : search_term,
        'sort_column' : sort,
        'user_list': users,
        'user': request.user,
    }
    return HttpResponse(template.render(context))


def collection_texts(request, collectionid):
    """
    List all of the texts that the user can see, with links to annotate them.
    """
    template = loader.get_template('annotations/collection_texts.html')
    order_by = request.GET.get('order_by', 'title')

    text_list = get_objects_for_user(request.user, 'annotations.view_text')
    text_list = text_list.filter(partOf=collectionid)
    text_list = text_list.order_by(order_by)

    N_relations = Relation.objects.filter(
        occursIn__partOf__id=collectionid).count()
    N_appellations = Appellation.objects.filter(
        occursIn__partOf__id=collectionid).count()

    # text_list = Text.objects.all()
    paginator = Paginator(text_list, 10)

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
        'order_by': order_by,
        'N_relations': N_relations,
        'N_appellations': N_appellations,
        'collection': TextCollection.objects.get(pk=collectionid)
    }
    return HttpResponse(template.render(context))


@ensure_csrf_cookie
def text(request, textid):
    """
    Provides the main text annotation view for logged-in users.
    Provides summary of the text for non-logged-in users.
    """

    text = get_object_or_404(Text, pk=textid)
    context_data = {
        'text': text,
        'textid': textid,
        'title': 'Annotate Text',
        'baselocation' : basepath(request)
    }

    # If a text is restricted, then the user needs explicit permission to
    #  access it.
    access_conditions = [
        'view_text' in get_perms(request.user, text),
        request.user in text.annotators.all(),
        getattr(request.user, 'is_admin', False),
        text.public,
    ]
    if not any(access_conditions):
        # TODO: return a pretty templated response.
        raise PermissionDenied

    if request.user.is_authenticated():
        template = loader.get_template('annotations/text.html')

        context_data['userid'] = request.user.id

        context = RequestContext(request, context_data)
        return HttpResponse(template.render(context))
    else:
        template = loader.get_template('annotations/anonymous_text.html')
        context = RequestContext(request, context_data)
        return HttpResponse(template.render(context))


def custom_403_handler(request):
    """
    Default 403 Handler. This method gets invoked if a PermissionDenied Exception is raised.
    Args:
        request: HttpRequest()

    Returns: HttpResponse() with status=403

    """
    template = loader.get_template('annotations/forbidden_error_page.html')
    context_data = {'userid': request.user.id,
                    'error_message': "Sorry you are not authorised to view this page."
                    }
    context = RequestContext(request, context_data)
    return HttpResponse(template.render(context), status=403)


### REST API class-based views.


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


class AppellationViewSet(AnnotationFilterMixin, viewsets.ModelViewSet):
    queryset = Appellation.objects.filter(asPredicate=False)
    serializer_class = AppellationSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )
    # pagination_class = LimitOffsetPagination

    def create(self, request, *args, **kwargs):
        data = request.data

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

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
            queryset = queryset.filter(ownedBy__pk=self.userid)
        else:
            queryset = queryset.filter(ownedBy__pk=self.request.user.id)
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
    queryset = Concept.objects.all()
    serializer_class = ConceptSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, )

    def create(self, request, *args, **kwargs):
        data = request.data
        if data['uri'] == 'generate':
            data['uri'] = 'http://vogonweb.net/{0}'.format(uuid.uuid4())

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
        uri = self.request.query_params.get('uri', None)
        type_uri = self.request.query_params.get('type_uri', None)
        max_results = self.request.query_params.get('max', None)

        if uri:
            queryset = queryset.filter(uri=uri)
        if type_uri:
            queryset = queryset.filter(type__uri=uri)
        if query:
            if pos == 'all':
                pos = None

            if remote:  # Spawn asynchronous calls to authority services.
                search_concept.delay(query, pos=pos)
            queryset = queryset.filter(label__icontains=query)

        if max_results:
            return queryset[:max_results]
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

            text = handle_file_upload(request, form)
            return HttpResponseRedirect(reverse('text', args=[text.id]))

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
    file_content = None
    if uploaded_file.content_type == 'text/plain':
        file_content = extract_text_file(uploaded_file)
    elif uploaded_file.content_type == 'application/pdf':
        file_content = extract_pdf_file(uploaded_file)

    # Save the content if the above extractors extracted something
    if file_content != None:
        tokenized_content = tokenize(file_content)
        return save_text_instance(tokenized_content, text_title, date_created, is_public, user)


def network_data(request):
    project = request.GET.get('project', None)
    user = request.GET.get('user', None)
    text = request.GET.get('text', None)

    queryset = Relation.objects.all()
    if project:
        queryset = queryset.filter(occursIn__partOf_id=project)
    if user:
        queryset = queryset.filter(createdBy_id=user)
    if text:
        queryset = queryset.filter(occursIn_id=text)


    nodes = OrderedDict()
    relations = OrderedDict()
    N = queryset.count()
    max_relation = 0.
    max_node = 0.
    for relation in queryset:
        source = relation.source.interpretation
        target = relation.object.interpretation
        key = tuple(sorted([source.id, target.id]))
        ids = {}
        for node in [source, target]:
            if node.id not in nodes:
                nodes[node.id] = {
                    'id': len(nodes),
                    'concept_id': node.id,
                    'label': node.label,
                    'weight': 1.,
                }
            else:
                nodes[node.id]['weight'] += 1.
            if nodes[node.id]['weight'] > max_node:
                max_node = nodes[node.id]['weight']

        if key in relations:
            relations[key]['weight'] += 1.
        else:
            relations[key] = {
                'source': nodes[source.id],
                'target': nodes[target.id],
                'id': relation.id,
                'weight': 1.,
            }
        if relations[key]['weight'] > max_relation:
            max_relation = relations[key]['weight']

    for key, relation in relations.items():
        relation['size'] = 3. * relation['weight']/max_relation
    for key, node in nodes.items():
        node['size'] = (4 + (2 * node['weight']))/max_node

    graph = igraph.Graph()
    graph.add_vertices(len(nodes))
    graph.add_edges([(relation['source']['id'], relation['target']['id']) for relation in relations.values()])
    layout = graph.layout_fruchterman_reingold()
    for i, coords in enumerate(layout._coords):
        nodes.values()[i]['x'] = coords[0] * 2
        nodes.values()[i]['y'] = coords[1] * 2


    return JsonResponse({'nodes': nodes.values(), 'edges': relations.values()})


@login_required
def add_text_to_collection(request, *args, **kwargs):
    # TODO: add exception handling.

    # if request.method == 'POST':
    text_id = request.GET.get('text', None)
    collection_id  = request.GET.get('collection', None)
    if text_id and collection_id:
        text = Text.objects.get(pk=text_id)
        collection = TextCollection.objects.get(pk=collection_id)
        collection.texts.add(text)
        collection.save()

    return JsonResponse({})


def user_details(request, userid, *args, **kwargs):
    """
    Provides users with their own profile view and public profile view of other users in case they are loggedIn.
    Provides users with public profile page in case they are not loggedIn
    ----------
    request : HTTPRequest
        The request for fetching user details
    userid : int
        The userid of user who's data  needs to be fetched
    args : list
        List of arguments to view
    kwargs : dict
        dict of arugments to view
    Returns
    ----------
    :HTTPResponse:
        Renders an user details view based on user's authentication status.
    """

    user = get_object_or_404(VogonUser, pk=userid)
    if request.user.is_authenticated() and request.user.id == userid:
        template = loader.get_template('annotations/user_details.html')
        context = RequestContext(request, {
            'user': request.user,
            'detail_user': user,
        })
    else:
        textCount = Text.objects.filter(addedBy=user).count()
        textAnnotated = Text.objects.filter(annotators=user).distinct().count()
        relation_count = user.relation_set.count()
        template = loader.get_template('annotations/user_details_public.html')
        context = RequestContext(request, {
            'detail_user': user,
            'textCount': textCount,
            'relation_count': relation_count,
            'textAnnotated': textAnnotated
        })
    return HttpResponse(template.render(context))


def list_collections(request, *args, **kwargs):
    queryset = TextCollection.objects.all()
    paginator = Paginator(queryset, 25)

    page = request.GET.get('page')
    try:
        collections = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        collections = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        collections = paginator.page(paginator.num_pages)

    template = loader.get_template('annotations/list_collections.html')
    context = RequestContext(request, {
        'user': request.user,
        'collections': collections
    })
    return HttpResponse(template.render(context))


def relation_details(request, concept_a_id, concept_b_id):
    concept_a = get_object_or_404(Concept, pk=concept_a_id)
    concept_b = get_object_or_404(Concept, pk=concept_b_id)

    queryset = Relation.objects.filter(
        Q(source__interpretation__id__in=[concept_a_id, concept_b_id]) \
        & Q(object__interpretation__id__in=[concept_a_id, concept_b_id]))


    template = loader.get_template('annotations/relations.html')
    context = RequestContext(request, {
        'user': request.user,
        'relations': queryset,
    })
    return HttpResponse(template.render(context))


def concept_details(request, conceptid):
    concept = get_object_or_404(Concept, pk=conceptid)
    appellations = Appellation.objects.filter(interpretation_id=conceptid)
    texts = set()
    appellations_by_text = OrderedDict()
    for appellation in appellations:
        text = appellation.occursIn
        texts.add(text)
        if text.id not in appellations_by_text:
            appellations_by_text[text.id] = []
        appellations_by_text[text.id].append(appellation)

    template = loader.get_template('annotations/concept_details.html')
    context = RequestContext(request, {
        'user': request.user,
        'concept': concept,
        'appellations': appellations_by_text,
        'texts': texts,
    })

    return HttpResponse(template.render(context))


# Not complete yet (threadsafe search)
class TextSearchView(SearchView):
    template = 'templates/search/search.html'
    queryset = SearchQuerySet().all()

    def get_queryset(self):
        queryset = super(TextSearchView, self).get_queryset()
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super(TextSearchView, self).get_context_data(*args, **kwargs)
        return context
