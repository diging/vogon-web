from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from django.contrib.contenttypes.models import ContentType
from django.template import RequestContext, loader
from annotations.models import VogonUser
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.files import File
from django.core.serializers import serialize
from django.core.cache import caches

from django.contrib.auth import login,authenticate
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect, csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic.edit import FormView

from django.conf import settings

from django.forms import formset_factory

from django.core.serializers import serialize
from django.db.models import Q, Count
from django.utils.safestring import mark_safe
from django.core.files import File
from guardian.shortcuts import get_objects_for_user, get_perms
from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.response import Response
from rest_framework.settings import api_settings
from django.db import models
from django.db.models.query import QuerySet

from rest_framework import viewsets, exceptions, status
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination

from guardian.shortcuts import get_objects_for_user

from concepts.models import Concept
from annotations.models import VogonUser
from annotations import quadriga
from concepts.authorities import search
from concepts.tasks import search_concept

from models import *
from forms import *
from serializers import *
from tasks import *

import hmac
import hashlib
from itertools import chain, combinations, groupby
from collections import OrderedDict, defaultdict, Counter
import requests
import re
from urlnorm import norm
from itertools import chain
import pytz
from django.db.models.expressions import DateTime
import uuid
import igraph
import copy
import datetime
from isoweek import Week

import os
from urlparse import urlparse
import urllib

import json
import time
from django.shortcuts import render
from hashlib import sha1
import base64
import logging
logger = logging.getLogger(__name__)
logger.setLevel('ERROR')

from haystack.generic_views import SearchView, FacetedSearchView
from haystack.query import SearchQuerySet

from repository.models import Repository


# TODO: Can we replace this with the built-in Django JsonResponse?
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
    template = loader.get_template('annotations/home.html')
    user_count = VogonUser.objects.filter(is_active=True).count()
    text_count = Text.objects.all().count()
    appellation_count = Appellation.objects.count()
    relation_count = Relation.objects.count()
    context = RequestContext(request, {
        'user_count': user_count,
        'text_count': text_count,
        'relation_count': relation_count,
        'appellation_count': appellation_count,
        'recent_combination': _get_recent_annotations(last=10),
        'title': 'Build the epistemic web'
    })
    return HttpResponse(template.render(context))




def basepath(request):
    """
    Generate the base path (domain + path) for the site.

    TODO: Do we need this anymore?

    Parameters
    ----------
    request : :class:`django.http.request.HttpRequest`

    Returns
    -------
    str
    """
    if request.is_secure():
        scheme = 'https://'
    else:
        scheme = 'http://'
    return scheme + request.get_host() + settings.SUBPATH


@csrf_protect
def register(request):
    """
    Provide new user registration view.

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
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
                link=form.cleaned_data['link'],
            )

            # TODO: Do we need this anymore?
            public, _ = Group.objects.get_or_create(name='Public')
            user.groups.add(public)
            user.save()    # TODO: redundant?

            new_user = authenticate(username=form.cleaned_data['username'],
                                    password=form.cleaned_data['password1'])
            # Logs in the new VogonUser.
            login(request, new_user)
            return HttpResponseRedirect(reverse('dashboard'))
    else:
        form = RegistrationForm()

    return render(request, 'registration/register.html', {'form': form})




@login_required
def user_projects(request):
    """
    Shows a list of the current (logged-in) uers's projects.
    """
    fields = [
        'id',
        'name',
        'created',
        'ownedBy__id',
        'ownedBy__username',
        'description',
        'num_texts',
        'num_relations',
    ]
    qs = TextCollection.objects.filter(ownedBy=request.user.id)
    qs = qs.annotate(num_texts=Count('texts'),
                     num_relations=Count('texts__relationsets'))
    qs = qs.values(*fields)

    template = loader.get_template('annotations/project_user.html')
    context = RequestContext(request, {
        'user': request.user,
        'title': 'Projects',
        'projects': qs,
    })
    return HttpResponse(template.render(context))


def view_project(request, project_id):
    """
    Shows details about a specific project owned by the current user.
    """

    project = get_object_or_404(TextCollection, pk=project_id)
    template = loader.get_template('annotations/project_details.html')

    order_by = request.GET.get('order_by', 'title')
    texts = project.texts.all().order_by(order_by).values('id', 'title', 'created')
    paginator = Paginator(texts, 15)

    page = request.GET.get('page')
    try:
        texts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        texts = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        texts = paginator.page(paginator.num_pages)


    context = RequestContext(request, {
        'user': request.user,
        'title': project.name,
        'project': project,
        'texts': texts,
    })

    return HttpResponse(template.render(context))


def create_project(request):

    return


@login_required
def edit_project(request, project_id):
    """
    Allow the owner of a project to edit it.
    """
    template = loader.get_template('annotations/project_change.html')
    project = get_object_or_404(TextCollection, pk=project_id)
    if project.ownedBy.id != request.user.id:
        raise PermissionDenied("Whoops, you're not supposed to be here!")

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('view_project', args=(project.id,)))
        else:
            print form.errors
    else:
        form = ProjectForm(instance=project)

    context = RequestContext(request, {
        'user': request.user,
        'title': 'Editing project: %s' % project.name,
        'project': project,
        'form': form,
        'page_title': 'Edit project'
    })
    return HttpResponse(template.render(context))


@login_required
def create_project(request):
    """
    Create a new project owned by the current (logged-in) user.
    """
    template = loader.get_template('annotations/project_change.html')

    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.ownedBy = request.user
            project.save()
            return HttpResponseRedirect(reverse('view_project', args=(project.id,)))
        else:
            print form.errors
    else:
        form = ProjectForm()

    context = RequestContext(request, {
        'user': request.user,
        'title': 'Create a new project',
        'form': form,
        'page_title': 'Create a new project'
    })
    return HttpResponse(template.render(context))


def list_projects(request):
    """
    All known projects.
    """

    fields = [
        'id',
        'name',
        'created',
        'ownedBy__id',
        'ownedBy__username',
        'description',
        'num_texts',
        'num_relations',
    ]
    qs = TextCollection.objects.all()
    qs = qs.annotate(num_texts=Count('texts'),
                     num_relations=Count('texts__relationsets'))
    qs = qs.values(*fields)

    template = loader.get_template('annotations/project_list.html')
    context = RequestContext(request, {
        'user': request.user,
        'title': 'Projects',
        'projects': qs,
    })
    return HttpResponse(template.render(context))


def user_recent_texts(user):
    """
    Return a list of :class:`.Text`\s recently annotated by a
    :class:`.VogonUser`\.

    TODO: Do we need this anymore?

    Parameters
    ----------
    user : :class:`.VogonUser`

    Returns
    -------
    list
    """
    by_appellations = user.appellation_set.all().order_by('-created').values_list('occursIn_id', 'occursIn__title', 'created')
    by_relations = user.relation_set.all().order_by('-created').values_list('occursIn_id', 'occursIn__title', 'created')
    # by_relations = Text.objects.filter(relation__createdBy__pk=user.id).values_list('id', 'title')
    # by_appellations = Text.objects.filter(appellation__createdBy__pk=user.id).values_list('id', 'title')
    results_sorted = sorted(chain([tuple(t) for t in by_relations], [tuple(t) for t in by_appellations]), key=lambda t: t[2])[::-1]
    results_unique = list(set([(t[0], t[1]) for t in results_sorted]))
    return results_unique


@login_required
def user_settings(request):
    """
    User profile settings.

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """

    if request.method == 'POST':
        form = UserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('user_details', args=[request.user.id]))
    else:
        form = UserChangeForm(instance=request.user)
        # Assign default image in the preview if no profile image is selected for the user.
        if request.user.imagefile == "" or request.user.imagefile is None:
            request.user.imagefile=settings.DEFAULT_USER_IMAGE

    template = loader.get_template('annotations/settings.html')
    context = RequestContext(request, {
        'user': request.user,
        'full_name' : request.user.full_name,
        'email' : request.user.email,
        'affiliation' : request.user.affiliation,
        'location' : request.user.location,
        'link' : request.user.link,
        'preview' : request.user.imagefile,
        'form': form,
        'subpath': settings.SUBPATH,
    })
    return HttpResponse(template.render(context))


def about(request):
    """
    Provides information about Vogon-Web

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """
    template = loader.get_template('annotations/about.html')
    context = RequestContext(request)
    context.update({
        'title': 'About VogonWeb'
    })
    return HttpResponse(template.render(context))


@login_required
def user_annotated_texts(request):
    recent_texts = user_recent_texts(request.user)

    context = RequestContext(request, {
        'title': 'My Texts',
        'user': request.user,
        'recent_texts': recent_texts,
        'added_texts': added_texts,
    })
    return HttpResponse(template.render(context))

@login_required
def dashboard(request):
    """
    Provides the user's personalized dashboard.

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """

    template = loader.get_template('annotations/dashboard.html')

    recent_texts = user_recent_texts(request.user)
    added_texts = Text.objects.filter(addedBy_id=request.user.id)\
                                .order_by('-added')\
                                .values_list('id', 'title', 'added')

    projects_owned = request.user.collections.all().values_list('id', 'name', 'description')
    projects_contributed = request.user.contributes_to.all().values_list('id', 'name', 'description')

    context = RequestContext(request, {
        'title': 'Dashboard',
        'user': request.user,
        'recent_texts': recent_texts[:5],
        'added_texts': added_texts[:5],
        'projects_owned': projects_owned[:5],
        'projects_contributed': projects_contributed[:5],
        'appellationCount': Appellation.objects.filter(createdBy__pk=request.user.id).filter(asPredicate=False).distinct().count(),
        'relation_count': Relation.objects.filter(createdBy__pk=request.user.id).distinct().count(),
    })
    return HttpResponse(template.render(context))


def network(request):
    """
    Provides a network browser view.

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """
    template = loader.get_template('annotations/network.html')
    form = RelationSetFilterForm(request.GET)
    context = {
        'baselocation': basepath(request),
        'user': request.user,
        'form': form,
    }
    return HttpResponse(template.render(context))


def list_texts(request):
    """
    List all of the texts that the user can see, with links to annotate them.

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """
    template = loader.get_template('annotations/list_texts.html')

    text_list = get_objects_for_user(request.user, 'annotations.view_text')
    order_by = request.GET.get('order_by', 'title')
    text_list = text_list.order_by(order_by).values('id', 'title', 'created')

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
        'title': 'Texts',
    }
    return HttpResponse(template.render(context))


def list_user(request):
    """
    List all the users of Vogon web.

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """

    template = loader.get_template('annotations/contributors.html')

    search_term = request.GET.get('search_term')
    sort = request.GET.get('sort', 'username')
    queryset = VogonUser.objects.exclude(id = -1).order_by(sort)

    if search_term:
        queryset = queryset.filter(Q(full_name__icontains=search_term) |
                                   Q(username__icontains=search_term))

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
        'title': 'Contributors'
    }
    return HttpResponse(template.render(context))


@csrf_exempt
def collection_texts(request, collectionid):
    """
    Texts for a particular collection.

    TODO: Do we need this anymore?

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """
    textcollectioninstance = TextCollection.objects.get(pk=collectionid)
    if request.method == 'POST':
        form = TextCollectionForm(request.POST,instance=textcollectioninstance)

        if form.is_valid():
            form.save()
    else:
        form=TextCollectionForm(instance=textcollectioninstance);

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
    paginator = Paginator(text_list, 20)

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
        'collection': TextCollection.objects.get(pk=collectionid),
        'form': form
    }
    return HttpResponse(template.render(context))


def _get_recent_annotations(last=20, user=None):
    """
    Generate aggregate activity feed for all annotations.

    TODO: move this into a util module.

    Parameters
    ----------
    last : int
        Number of items to return (default: 20).
    user : :class:`.VogonUser`

    Returns
    -------
    dict
    """
    recent_appellations = Appellation.objects.all()
    recent_relations = Relation.objects.all()

    if user:
        recent_appellations = recent_appellations.filter(createdBy_id=user.id)
        recent_relations = recent_relations.filter(createdBy_id=user.id)

    recent_appellations = recent_appellations.annotate(hour=DateTime("created", "hour", pytz.timezone("UTC")))\
        .values("hour", "createdBy__username", "createdBy__id")\
        .annotate(appelation_count=Count('id'))\
        .order_by("-hour")
    recent_relations = recent_relations.annotate(hour=DateTime("created", "hour", pytz.timezone("UTC")))\
        .values("hour", "createdBy__username", "createdBy__id")\
        .annotate(relation_count=Count('id'))\
        .order_by("-hour")

    combined_data = OrderedDict()
    for event in recent_appellations:
        key = (event['hour'], event['createdBy__username'], event['createdBy__id'])
        if key not in combined_data:
            combined_data[key] = {'appelation_count': event['appelation_count'], 'relation_count': 0}
        combined_data[key]['appelation_count'] += event['appelation_count']
    for event in recent_relations:
        key = (event['hour'], event['createdBy__username'], event['createdBy__id'])
        if key not in combined_data:
            combined_data[key] = {'appelation_count': 0, 'relation_count': event['relation_count']}
        combined_data[key]['relation_count'] += event['relation_count']
    return dict(sorted(combined_data.items(), key=lambda k: k[0][0])[::-1][:last])


def _get_recent_annotations_for_graph(annotation_by_user, start_date):
    result = dict()
    weeks_last_date_map = dict()
    d7 = datetime.timedelta( days = 7)
    current_week = datetime.datetime.now() + d7

    # Find out the weeks and their last date in the past 90 days.
    while start_date <= current_week:
        result[(Week(start_date.isocalendar()[0], start_date.isocalendar()[1]).saturday()).strftime('%m-%d-%y')] = 0
        start_date += d7
    time_format = '%Y-%m-%d'

    # Count annotations for each week.
    for count_per_day in annotation_by_user:
        if(isinstance(count_per_day['date'], unicode)):
            date = datetime.datetime.strptime(count_per_day['date'], time_format)
        else:
            date = count_per_day['date']
        result[(Week(date.isocalendar()[0], date.isocalendar()[1]).saturday()).strftime('%m-%d-%y')] += count_per_day['count']
    annotation_per_week = list()

    # Sort the date and format the data in the format required by d3.js.
    keys = (result.keys())
    keys.sort()
    for key in keys:
        new_format = dict()
        new_format["date"] = key
        new_format["count"] = result[key]
        annotation_per_week.append(new_format)
    annotation_per_week = str(annotation_per_week).replace("'", "\"")
    return annotation_per_week


def _get_appellations_data(appellations):
    """
    Generate appellation summary information for display in the text detail
    view.
    """
    appellations = appellations.order_by('interpretation_id')

    fields = [
        'interpretation_id',
        'interpretation__label',
        'interpretation__typed__label',
        'interpretation__merged_with_id',
        'interpretation__merged_with__label',
        'interpretation__merged_with__typed__label',
        'occursIn_id',
        'occursIn__tokenizedContent',
        'tokenIds',
        'createdBy_id',
        'createdBy__username',
        'created',
    ]

    appellations = appellations.values(*fields)
    appellations_data = []

    appellation_creators = set()
    groupkey = lambda a: a['interpretation__merged_with_id'] if a['interpretation__merged_with_id'] else a['interpretation_id']
    for concept_id, concept_appellations in groupby(appellations, groupkey):
        indiv_appellations = []
        unique_texts = set()
        for i, appellation in enumerate(concept_appellations):
            # We have to do this in here, because ``appellation`` is a
            #  itertools._grouper iterable.
            if i == 0:
                if appellation['interpretation__merged_with__typed__label']:
                    type_label = appellation['interpretation__merged_with__typed__label']
                elif appellation['interpretation__typed__label']:
                    type_label = appellation['interpretation__typed__label']
                else:
                    type_label = u''
                if appellation['interpretation__merged_with__label']:
                    concept_label = appellation['interpretation__merged_with__label']
                else:
                    concept_label = appellation['interpretation__label']

            indiv_appellations.append({
                "text_snippet": get_snippet(appellation),
                "annotator_id": appellation['createdBy_id'],
                "annotator_username": appellation['createdBy__username'],
                "created": appellation['created'],
            })
            appellation_creators.add(appellation['createdBy_id'])
            unique_texts.add(appellation['occursIn_id'])

        num_texts = len(unique_texts) - 1
        appellations_data.append({
            "interpretation_id": concept_id,
            "interpretation_label": concept_label,
            "interpretation_type": type_label,
            "appellations": indiv_appellations,
            "num_texts": num_texts,
        })

    appellations_data = sorted(appellations_data,
                               key=lambda a: a['interpretation_label'])

    return appellations_data, appellation_creators


def _get_relations_data(relationset_qs):
    """
    Organize RelationSets for this text so that we can display them in
    conjunction with edges in the graph. In other words, grouped by
    the "source" and "target" of the simplified graphical representation.
    """

    app_ct = ContentType.objects.get_for_model(Appellation)
    relationsets_by_interpretation = []
    relationsets = []

    fields = [
        'source_content_type_id',
        'object_content_type_id',
        'source_object_id',
        'object_object_id',
        'predicate__tokenIds',
        'predicate__interpretation__label',
        'predicate__interpretation_id',
    ]

    # Pull out "focal" concepts from the RelationSet. Usually there will
    #  be only two, but there could be more.
    for relationset in relationset_qs:
        appellation_ids = set()
        for rel in relationset.constituents.all().values(*fields):
            for part in ['source', 'object']:
                if rel.get('%s_content_type_id' % part, None) == app_ct.id:
                    appellation_ids.add(rel['%s_object_id' % part])

        interps = []    # Focal concepts go here.
        appellations = Appellation.objects.filter(pk__in=appellation_ids, asPredicate=False)
        appellation_fields = [
            'interpretation_id',
            'interpretation__label',
            'interpretation__typed__label',
            'interpretation__merged_with_id',
            'interpretation__merged_with__label',
            'interpretation__merged_with__typed__label',
        ]
        for appellation in appellations.values(*appellation_fields):
            if appellation['interpretation__merged_with_id']:
                interps.append((appellation['interpretation__merged_with_id'], appellation['interpretation__merged_with__label']))
            else:
                interps.append((appellation['interpretation_id'], appellation['interpretation__label']))

        # Usually there will be only two Concepts here, but for more complex
        #  relations there could be more.
        for u, v in combinations(interps, 2):
            u, v = tuple(sorted([u, v], key=lambda a: a[0]))
            # This is kind of hacky, but it lets us access the IDs and
            #  labels more readily below.
            rset = ((u[0], u[1], v[0], v[1]), relationset)
            relationsets_by_interpretation.append(rset)

    # Here we sort and group by concept-pairs (u and v, above).
    skey = lambda r: r[0]
    rsets = groupby(sorted(relationsets_by_interpretation, key=skey),
                    key=skey)

    # Each group will be shown as an accordion panel in the view.
    for (u_id, u_label, v_id, v_label), i_relationsets in rsets:
        relationsets.append({
            "source_interpretation_id": u_id,
            "source_interpretation_label": u_label,
            "target_interpretation_id": v_id,
            "target_interpretation_label": v_label,
            "relationsets": [{
                "text_snippet": get_snippet_relation(relationset),
                "annotator": relationset.createdBy,
                "created": relationset.created,
            } for _, relationset in i_relationsets]
        })
    return relationsets


def recent_activity(request):
    """
    Provides summary of activities performed on the system.
    Currently on text addition, Appellation additions are shown.

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """
    template = loader.get_template('annotations/recent_activity.html')
    recent_texts = Text.objects.annotate(hour=DateTime("added", "hour", pytz.timezone("UTC"))).values("hour", "addedBy__username").annotate(created_count=Count('id')).order_by("-hour", "addedBy")

    context = {
        'recent_texts': recent_texts,
        'recent_combination': _get_recent_annotations()
    }
    return HttpResponse(template.render(context))


@ensure_csrf_cookie
def text(request, textid):
    """
    Provides the main text view.

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
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
    # if not any(access_conditions):
    #     # TODO: return a pretty templated response.
    #     raise PermissionDenied
    mode = request.GET.get('mode', 'view')

    if all([request.user.is_authenticated(), any(access_conditions), mode == 'annotate']):
        template = loader.get_template('annotations/text.html')
        context_data.update({
            'userid': request.user.id,
            'title': text.title,
        })
        context = RequestContext(request, context_data)
        return HttpResponse(template.render(context))
    elif all([request.user.is_authenticated(), any(access_conditions), mode == 'user_annotations']):
        appellations = Appellation.objects.filter(occursIn_id=textid,
                                                  asPredicate=False,
                                                  createdBy=request.user.id)
        appellations_data, appellation_creators = _get_appellations_data(appellations)
        relationset_qs = RelationSet.objects.filter(occursIn=textid,
                                                    createdBy=request.user.id)
        relationsets = _get_relations_data(relationset_qs)

        context_data.update({
            'view': 'user',
        })
    elif mode == 'annotate':
        return HttpResponseRedirect(reverse('login'))

    # TODO: pull most of this logic out into helper functions, and move it
    #  out of views.py.

    template = loader.get_template('annotations/text_view.html')

    appellations = Appellation.objects.filter(occursIn_id=textid,
                                              asPredicate=False)
    appellations_data, appellation_creators = _get_appellations_data(appellations)
    relationset_qs = RelationSet.objects.filter(occursIn=textid)
    relationsets = _get_relations_data(relationset_qs)


    context_data.update({
        'userid': request.user.id,
        'appellations_data': appellations_data,
        'annotators': appellation_creators,
        'relations': relationsets,
        'title': text.title,
    })
    context = RequestContext(request, context_data)
    return HttpResponse(template.render(context))


# TODO: move this out of views.py and into an exceptions module.
def custom_403_handler(request):
    """
    Default 403 Handler. This method gets invoked if a PermissionDenied
    Exception is raised.

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
        Status 403.
    """
    template = loader.get_template('annotations/forbidden_error_page.html')
    context_data = {
        'userid': request.user.id,
        'error_message': "Whoops, you're not supposed to be here!"
    }
    context = RequestContext(request, context_data)
    return HttpResponse(template.render(context), status=403)


### REST API class-based views.
#
# TODO: move these CBVs into their own module.
#


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
    request : `django.http.requests.HttpRequest`

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """

    project_id = request.GET.get('project', None)

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        form.fields['project'].queryset = form.fields['project'].queryset.filter(ownedBy_id=request.user.id)
        if form.is_valid():

            text = handle_file_upload(request, form)
            return HttpResponseRedirect(reverse('text', args=[text.id]) + u'?mode=annotate')
    else:
        form = UploadFileForm()

        form.fields['project'].queryset = form.fields['project'].queryset.filter(ownedBy_id=request.user.id)
        if project_id:
            form.fields['project'].initial = project_id

    template = loader.get_template('annotations/upload_file.html')
    context = RequestContext(request, {
        'user': request.user,
        'form': form,
        'subpath': settings.SUBPATH,
        'repositories': Repository.objects.all(),
    })
    return HttpResponse(template.render(context))


def handle_file_upload(request, form):
    """
    Handle the uploaded file and route it to corresponding handlers

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`
    form : `django.forms.Form`
        The form with uploaded content

    """
    uploaded_file = request.FILES['filetoupload']
    uri = form.cleaned_data['uri']
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
        return save_text_instance(tokenized_content, text_title, date_created, is_public, user, uri)


def _filter_relationset(qs, params):
    """

    TODO: move this out of views.py and into an util module.
    """
    parameter_map = [
        ('text', 'occursIn_id__in'),
        ('project', 'occursIn__partOf__in'),
        ('text_published_from', 'occursIn__created__gte'),
        ('text_published_through', 'occursIn__created__lte'),
        ('user', 'createdBy__in'),
        ('created_from', 'created__gte'),
        ('created_through', 'created__lte'),
    ]

    parameters = {}
    for param, field in parameter_map:
        if param in ['text', 'project', 'user']:
            value = params.getlist(param, [])
        else:
            value = params.get(param, None)
        if value and value[0]:
            parameters[field] = value

    qs = qs.filter(**parameters)

    node_types = params.getlist('node_types')
    exclusive = params.get('exclusive', 'off')

    # We need this ContentType to filter on Relations, since .source and .object
    #  are Generic relations.
    app_ct = ContentType.objects.get_for_model(Appellation)

    # Limit to RelationSets whose Appellations refer to Concepts of a
    #  specific Type.
    if node_types:
        appellations = Appellation.objects.filter(**parameters).filter(interpretation__typed__in=node_types).values_list('id', flat=True)
        q_source = Q(constituents__source_content_type=app_ct) & Q(constituents__source_object_id__in=appellations)
        q_object = Q(constituents__object_content_type=app_ct) & Q(constituents__object_object_id__in=appellations)
        if exclusive == 'on':
            q = q_source & q_object
        else:
            q = q_source | q_object
        qs = qs.filter(q)

    # Limit to RelationSets whose Appellations refer to specific Concepts.
    nodes = params.getlist('nodes')

    if nodes:
        appellations = Appellation.objects.filter(**parameters).filter(interpretation__in=nodes).values_list('id', flat=True)
        q = (Q(constituents__source_content_type=app_ct) & Q(constituents__source_object_id__in=appellations)|
             Q(constituents__object_content_type=app_ct) & Q(constituents__object_object_id__in=appellations))
        qs = qs.filter(q)

    # We have filtered based on related fields, which means that if we were to
    #  call values() or values_list() on those related fields we would be
    #  limited not only to the selected RelationSets but also to the specific
    #  passing values. Re-filtering based on ID ensures that we can get all of
    #  the relevant related fields for the RelationSets in our QuerySet.
    return RelationSet.objects.filter(id__in=qs.values_list('id', flat=True))


def network_data(request):
    """
    Generates JSON data for Cytoscape.js graph visualization.
    """
    # project = request.GET.get('project', None)
    # user = request.GET.get('user', None)
    # text = request.GET.get('text', None)

    cache_key = request.get_full_path()
    cache = caches['default']

    response_data = cache.get(cache_key)
    if not response_data:
        queryset = _filter_relationset(RelationSet.objects.all(), request.GET)
        # if project:
        #     queryset = queryset.filter(occursIn__partOf_id=project)
        # if user:
        #     queryset = queryset.filter(createdBy_id=user)
        # if text:
        #     queryset = queryset.filter(occursIn_id=text)

        nodes, edges = generate_network_data(queryset)
        nodes_rebased = {}
        edges_rebased = {}
        node_lookup = {}
        max_edge = 0.
        max_node = 0.
        for i, node in enumerate(nodes.values()):
            ogn_id = copy.deepcopy(node['data']['id'])
            nodes_rebased[i] = copy.deepcopy(node)
            # nodes_rebased[i].update({'id': i})
            nodes_rebased[i]['data']['id'] = i
            nodes_rebased[i]['data']['concept_id'] = ogn_id

            node_lookup[ogn_id] = i

            if node['data']['weight'] > max_node:
                max_node = node['data']['weight']
        for i, edge in enumerate(edges.values()):
            ogn_id = copy.deepcopy(edge['data']['id'])
            edges_rebased[i] = copy.deepcopy(edge)

            edges_rebased[i]['data'].update({'id': i + len(nodes_rebased)})
            edges_rebased[i]['data']['source'] = nodes_rebased[node_lookup[edge['data']['source']]]['data']['id']
            edges_rebased[i]['data']['target'] = nodes_rebased[node_lookup[edge['data']['target']]]['data']['id']
            if edge['data']['weight'] > max_edge:
                max_edge = edge['data']['weight']

        for edge in edges_rebased.values():
            edge['data']['weight'] = edge['data']['weight']/max_edge
        for node in nodes_rebased.values():
            node['data']['weight'] = (50 + (2 * node['data']['weight']))/max_node

        graph = igraph.Graph()
        graph.add_vertices(len(nodes_rebased))

        graph.add_edges([(relation['data']['source'], relation['data']['target'])
                         for relation in edges_rebased.values()])
        layout = graph.layout_graphopt()
        # layout = graph.layout_fruchterman_reingold(maxiter=500)

        for coords, node in zip(layout._coords, nodes_rebased.values()):
            node['data']['pos'] = {
                'x': coords[0] * 5,
                'y': coords[1] * 5
            }

        response_data = {'elements': nodes_rebased.values() + edges_rebased.values()}
        cache.set(cache_key, response_data, 300)
    return JsonResponse(response_data)


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
    if request.user.is_authenticated() and request.user.id == int(userid) and request.GET.get('mode', '') == 'edit':
        return HttpResponseRedirect(reverse('settings'))
    else:
        textCount = Text.objects.filter(addedBy=user).count()
        textAnnotated = Text.objects.filter(appellation__createdBy=user).distinct().count()
        relation_count = user.relation_set.count()
        appellation_count = user.appellation_set.count()
        start_date = datetime.datetime.now() + datetime.timedelta(-60)

        # Count annotations for user by date.
        relations_by_user = Relation.objects.filter(createdBy = user, created__gt = start_date)\
            .extra({'date' : 'date(created)'}).values('date').annotate(count = Count('created'))

        appelations_by_user = Appellation.objects.filter(createdBy = user, created__gt = start_date)\
            .extra({'date' : 'date(created)'}).values('date').annotate(count = Count('created'))

        annotation_by_user = list(relations_by_user)
        annotation_by_user.extend(list(appelations_by_user))

        result = dict()
        weeks_last_date_map = dict()
        d7 = datetime.timedelta( days = 7)
        current_week = datetime.datetime.now() + d7

        # Find out the weeks and their last date in the past 90 days.
        while start_date <= current_week:
            result[(Week(start_date.isocalendar()[0], start_date.isocalendar()[1]).saturday()).strftime('%m-%d-%y')] = 0
            start_date += d7
        time_format = '%Y-%m-%d'

        # Count annotations for each week.
        for count_per_day in annotation_by_user:
            if(isinstance(count_per_day['date'], unicode)):
                date = datetime.datetime.strptime(count_per_day['date'], time_format)
            else:
                date = count_per_day['date']
            result[(Week(date.isocalendar()[0], date.isocalendar()[1]).saturday()).strftime('%m-%d-%y')] += count_per_day['count']
        annotation_per_week = list()

        # Sort the date and format the data in the format required by d3.js.
        keys = (result.keys())
        keys.sort()
        for key in keys:
            new_format = dict()
            new_format["date"] = key
            new_format["count"] = result[key]
            annotation_per_week.append(new_format)
        annotation_per_week = str(annotation_per_week).replace("'", "\"")

        projects = user.collections.all()

        template = loader.get_template('annotations/user_details_public.html')
        context = RequestContext(request, {
            'detail_user': user,
            'textCount': textCount,
            'relation_count': relation_count,
            'appellation_count': appellation_count,
            'text_count': textAnnotated,
            'default_user_image' : settings.DEFAULT_USER_IMAGE,
            'annotation_per_week' : annotation_per_week,
            'recent_activity': _get_recent_annotations(user=user),
            'projects': projects,
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


def relation_details(request, source_concept_id, target_concept_id):
    source_concept = get_object_or_404(Concept, pk=source_concept_id)
    target_concept = get_object_or_404(Concept, pk=target_concept_id)

    # Source and target on Relation are now generic, so we need this for lookup.
    appellation_type = ContentType.objects.get_for_model(Appellation)

    source_appellation_ids = Appellation.objects.filter(interpretation=source_concept.id).values_list('id', flat=True)
    target_appellation_ids = Appellation.objects.filter(interpretation=target_concept.id).values_list('id', flat=True)
    q = ((Q(constituents__source_object_id__in=source_appellation_ids) & Q(constituents__source_content_type=appellation_type)) |
         (Q(constituents__object_object_id__in=source_appellation_ids) & Q(constituents__object_content_type=appellation_type)))
    source_queryset = RelationSet.objects.filter(id__in=RelationSet.objects.filter(q).values_list('id', flat=True))

    q = ((Q(constituents__source_object_id__in=target_appellation_ids) & Q(constituents__source_content_type=appellation_type)) |
         (Q(constituents__object_object_id__in=target_appellation_ids) & Q(constituents__object_content_type=appellation_type)))
    combined_queryset = RelationSet.objects.filter(id__in=source_queryset.filter(q).values_list('id', flat=True))

    template = loader.get_template('annotations/relations.html')

    relationsets = []
    for text_id, text_relationsets in groupby(combined_queryset, lambda a: a.occursIn.id):
        text = Text.objects.get(pk=text_id)
        relationsets.append({
            "text_id": text.id,
            "text_title": text.title,
            "relationsets": [{
                "text_snippet": get_snippet_relation(relationset),
                "annotator": relationset.createdBy,
                "created": relationset.created,
            } for relationset in text_relationsets]
        })

    context = RequestContext(request, {
        'user': request.user,
        'source_concept': source_concept,
        'target_concept': target_concept,
        'relations': relationsets,
    })
    return HttpResponse(template.render(context))


def concept_details(request, conceptid):
    concept = get_object_or_404(Concept, pk=conceptid)
    appellations = Appellation.objects.filter(interpretation_id=conceptid)

    fields = [
        'id',
        'occursIn_id',
        'occursIn__title',
        'occursIn__tokenizedContent',
        'tokenIds',
        'createdBy_id',
        'createdBy__username',
        'created'
    ]

    appellations = appellations.values(*fields)

    response_format = request.GET.get('format', None)
    response = dict()
    concept_details = []
    appellations_by_text = dict()
    text = ""
    for text_id, text_appellations in groupby(appellations, lambda a: a['occursIn_id']):
        appellation_details = []
        for i, appellation in enumerate(text_appellations):
            if i == 0:
                text_title = appellation['occursIn__title']

            appellation_details.append({
                "text_snippet": get_snippet(appellation),
                "annotator_id": appellation['createdBy_id'],
                "annotator_username": appellation['createdBy__username'],
                "created": appellation['created'],
            })

        concept_details.append({
            "text_id": text_id,
            "text_title": text_title,
            "appellations": appellation_details
        })
    response["texts"] = concept_details
    if response_format == 'json':
        response["concept_label"] = concept.label
        response["concept_uri"] = concept.uri
        response["concept_description"] = concept.description
        return JsonResponse(response)
    else:
        response['concept'] = concept
        template = loader.get_template('annotations/concept_details.html')
        context = RequestContext(request, response)
        return HttpResponse(template.render(context))

@staff_member_required
def add_relationtemplate(request):
    """
    Staff can use this view to create :class:`.RelationTemplate`\s.
    """

    # Each RelationTemplatePart is a "triple", the subject or object of which
    #  might be another RelationTemplatePart.
    formset = formset_factory(RelationTemplatePartForm, formset=RelationTemplatePartFormSet)
    form_class = RelationTemplateForm   # e.g. Name, Description.

    context = {}
    error = None    # TODO: <-- make this less hacky.
    if request.POST:
        logger.debug('add_relationtemplate: post request')

        # Instatiate both form(set)s with data.
        relationtemplatepart_formset = formset(request.POST, prefix='parts')
        relationtemplate_form = form_class(request.POST)
        context['formset'] = relationtemplatepart_formset
        context['templateform'] = relationtemplate_form

        if relationtemplatepart_formset.is_valid() and relationtemplate_form.is_valid():
            logger.debug('add_relationtemplate: both forms are valid')
            # We commit the RelationTemplate to the database first, so that we
            #  can use it in the FK relation ``RelationTemplatePart.part_of``.
            relationTemplate = relationtemplate_form.save()

            # We index RTPs so that we can fill FK references among them.
            relationTemplateParts = {}
            dependency_order = {}    # Source RTP index -> target RTP index.
            for form in relationtemplatepart_formset:
                relationTemplatePart = RelationTemplatePart()
                relationTemplatePart.part_of = relationTemplate
                relationTemplatePart.internal_id = form.cleaned_data['internal_id']

                # Since many field names are shared for source, predicate, and
                #  object, this approach should cut down on a lot of repetitive
                #  code.
                for part in ['source', 'predicate', 'object']:
                    setattr(relationTemplatePart, part + '_node_type',
                            form.cleaned_data[part + '_node_type'])
                    setattr(relationTemplatePart, part + '_prompt_text',
                            form.cleaned_data[part + '_prompt_text'])
                    setattr(relationTemplatePart, part + '_label',
                            form.cleaned_data[part + '_label'])

                    # Node is a concept Type. e.g. ``E20 Person``.
                    if form.cleaned_data[part + '_node_type'] == 'TP':
                        setattr(relationTemplatePart, part + '_type',
                                form.cleaned_data[part + '_type'])
                        setattr(relationTemplatePart, part + '_description',
                                form.cleaned_data[part + '_description'])

                    # Node is a specific Concept, e.g. ``employ``.
                    elif form.cleaned_data[part + '_node_type'] == 'CO':
                        setattr(relationTemplatePart, part + '_concept',
                                form.cleaned_data[part + '_concept'])
                        # We may still want to provide instructions to the user
                        #  via the description field.
                        setattr(relationTemplatePart, part + '_description',
                                form.cleaned_data[part + '_description'])

                    # Node is another RelationTemplatePart.
                    elif form.cleaned_data[part + '_node_type'] == 'RE':
                        target_id = form.cleaned_data[part + '_relationtemplate_internal_id']
                        setattr(relationTemplatePart,
                                part + '_relationtemplate_internal_id',
                                target_id)
                        if target_id > -1:
                            # This will help us to figure out the order in
                            #  which to save RTPs.
                            dependency_order[relationTemplatePart.internal_id] = target_id

                # Index so that we can fill FK references among RTPs.
                relationTemplateParts[relationTemplatePart.internal_id] = relationTemplatePart

            # If there is interdependency among RTPs, determine and execute
            #  the correct save order.
            if len(dependency_order) > 0:
                # Find the relation template furthest downstream.
                # TODO: is this really better than hitting the database twice?
                start_rtp = copy.deepcopy(dependency_order.keys()[0])
                this_rtp = copy.deepcopy(start_rtp)
                save_order = [this_rtp]
                iteration = 0
                while True:
                    this_rtp = copy.deepcopy(dependency_order[this_rtp])
                    if this_rtp not in save_order:
                        save_order.insert(0, copy.deepcopy(this_rtp))
                    if this_rtp in dependency_order:
                        iteration += 1
                    else:   # Found the downstream relation template.
                        break

                    # Make sure that we're not in an endless loop.
                    # TODO: This is kind of a hacky way to handle the situation.
                    #  Maybe we should move this logic to the validation phase,
                    #  so that we can handle errors in a Django-esque fashion.
                    if iteration > 0 and this_rtp == start_rtp:
                        error = 'Endless loop'
                        break
                if not error:
                    # Resolve internal ids for RTP references into instance pks,
                    #  and populate the RTP _relationtemplate fields.
                    for i in save_order:
                        for part in ['source', 'object']:
                            dep = getattr(relationTemplateParts[i],
                                          part + '_relationtemplate_internal_id')
                            if dep > -1:
                                setattr(relationTemplateParts[i],
                                        part + '_relationtemplate',
                                        relationTemplateParts[dep])
                        # Only save non-committed instances.
                        if not relationTemplateParts[i].id:
                            relationTemplateParts[i].save()

            # Otherwise, just save the (one and only) RTP.
            elif len(relationTemplateParts) == 1:
                relationTemplateParts.values()[0].save()

            if not error:
                # TODO: when the list view for RTs is implemented, we should
                #  direct the user there.
                return HttpResponseRedirect(reverse('list_relationtemplate'))

            else:
                # For now, we can render this view-wide error separately. But
                #  we should probably make this part of the normal validation
                #  process in the future. See comments above.
                context['error'] = error
        else:
            logger.debug('add_relationtemplate: forms not valid')
            context['formset'] = relationtemplatepart_formset
            context['templateform'] = relationtemplate_form

    else:   # No data, start with a fresh formset.
        context['formset'] = formset(prefix='parts')
        context['templateform'] = form_class()

    return render(request, 'annotations/relationtemplate.html', context)


@login_required
def list_relationtemplate(request):
    """
    Returns a list of all :class:`.RelationTemplate`\s.
    """
    queryset = RelationTemplate.objects.all()
    search = request.GET.get('search', None)
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )

    data = {
        'templates': [{
            'id': rt.id,
            'name': rt.name,
            'description': rt.description,
            'fields': rt.fields,
            } for rt in queryset]
        }

    response_format = request.GET.get('format', None)
    if response_format == 'json':
        return JsonResponse(data)

    template = loader.get_template('annotations/relationtemplate_list.html')
    context = RequestContext(request, {
        'user': request.user,
        'data': data,
    })

    return HttpResponse(template.render(context))


class TextSearchView(FacetedSearchView):
    """Class based view for thread-safe search."""
    facet_fields = ['collections']
    template_name = 'annotations/list_texts.html'
    queryset = SearchQuerySet().models(Text)
    results_per_page = 20


    def get_context_data(self, *args, **kwargs):
        """Return context data."""
        context = super(TextSearchView, self).get_context_data(*args, **kwargs)
        sort_base = self.request.get_full_path().split('?')[0]
        if 'query' in context and context['query']:
            sort_base += '?q=' + context['query']



        context.update({
            'sort_base': sort_base,

        })
        return context



    def form_valid(self, form):
        order_by = self.request.GET.get('order_by', 'title')

        # If there is no query, just show all of the texts.
        q = form.cleaned_data.get(self.search_field)
        query_for_display = q
        if not q:
            q = '*'
            query_for_display = ''
        form.cleaned_data[self.search_field] = q

        self.queryset = form.search().order_by(order_by)
        queryset = self.queryset
        # else:
        #     params = self.request.GET.getlist('selected_facets')
        #     queryset = self.get_queryset().order_by(order_by)

        context = self.get_context_data(**{
            self.form_name: form,
            'query': query_for_display, #form.cleaned_data.get(self.search_field),
            'object_list': queryset,
            'order_by': order_by,
        })

        return self.render_to_response(context)

    def form_invalid(self, form):
        """
        Just return all of the texts.
        """

        order_by = self.request.GET.get('order_by', 'title')
        sqs = self.get_queryset()

        # Facet the hell out of those texts.
        self.selected_facets = self.request.GET.getlist('selected_facets', [])
        for facet in self.selected_facets:
            if ":" not in facet:
                continue
            field, value = facet.split(":", 1)
            if value:
                sqs = sqs.narrow(u'%s:"%s"' % (field, sqs.query.clean(value)))

        context = self.get_context_data(**{
            self.form_name: form,
            'query': '',
            'object_list': sqs.order_by(order_by),
            'order_by': order_by,

        })
        # Goddammit.
        context.update({'facets': sqs.facet_counts()})

        return self.render_to_response(context)


@login_required
def get_relationtemplate(request, template_id):
    """
    Returns data on fillable fields in a :class:`.RelationTemplate`\.
    """

    relation_template = get_object_or_404(RelationTemplate, pk=template_id)

    data = {
        'fields': relation_template.fields,
        'name': relation_template.name,
        'description': relation_template.description,
        'id': template_id,
        'expression': relation_template.expression,
    }
    response_format = request.GET.get('format', None)
    if response_format == 'json':
        return JsonResponse(data)

    template = loader.get_template('annotations/relationtemplate_show.html')
    context = RequestContext(request, {
        'user': request.user,
        'data': data,
    })

    return HttpResponse(template.render(context))


@login_required
def create_from_relationtemplate(request, template_id):
    """
    Create a :class:`.RelationSet` and constituent :class:`.Relation`\s from
    a :class:`.RelationTemplate` and user annotations.

    This is mainly used by the RelationTemplateController in the text
    annotation  view.
    """

    template = get_object_or_404(RelationTemplate, pk=template_id)

    # Index RelationTemplateParts by ID.
    template_parts = {part.id: part for part in template.template_parts.all()}

    if request.POST:
        relations = {}
        data = json.loads(request.body)

        relation_data = {}
        for field in data['fields']:

            if field['part_id'] not in relation_data:
                relation_data[int(field['part_id'])] = {}
            relation_data[int(field['part_id'])][field['part_field']] = field

        relation_set = RelationSet(
            template=template,
            createdBy=request.user,
            occursIn_id=data['occursIn'],
        )
        relation_set.save()

        def create_appellation(field_data, template_part, field, evidence_required=True):
            node_type = getattr(template_part, '%s_node_type' % field)

            appellation_data = {
                'occursIn_id': data['occursIn'],
                'createdBy_id': request.user.id,
            }
            if evidence_required and field_data:
                appellation_data.update({
                    'tokenIds': field_data['data']['tokenIds'],
                    'stringRep': field_data['data']['stringRep'],
                })
            else:
                appellation_data.update({'asPredicate': True})

            if node_type == RelationTemplatePart.CONCEPT:
                # The interpretation is already provided.
                interpretation = getattr(template_part, '%s_concept' % field)

            # TODO: these should not be hard-coded. Add these URIs to config.
            elif node_type == RelationTemplatePart.TOBE:
                interpretation = Concept.objects.get(uri="http://www.digitalhps.org/concepts/CON3fbc4870-6028-4255-9998-14acf028a316")
            elif node_type == RelationTemplatePart.HAS:
                interpretation = Concept.objects.get(uri="http://www.digitalhps.org/concepts/CON83f5110b-5034-4c95-82f8-8f80ff55a1b9")
            if interpretation:
                appellation_data.update({'interpretation': interpretation})

            if field == 'predicate':
                appellation_data.update({'asPredicate': True})
            appellation = Appellation(**appellation_data)
            appellation.save()
            return appellation

        relation_dependency_graph = nx.DiGraph()


        # Since we don't know anything about the structure of the
        #  RelationTemplate, we watch for nodes that expect to be Relation
        #  instances and recurse to create them as needed. We store the results
        #  for each Relation in ``relation_data_processed`` so that we don't
        #  create duplicate Relation instances.
        relation_data_processed = {}
        def process_recurse(part_id, template_part):
            """

            Returns
            -------
            relation_id : int
            relation : :class:`.Relation`
            """

            if part_id in relation_data_processed:
                return relation_data_processed[part_id]

            part_data = {
                'createdBy': request.user,
                'occursIn_id': data['occursIn']
            }
            for field in ['source', 'predicate', 'object']:

                node_type = getattr(template_part, '%s_node_type' % field)
                evidence_required = getattr(template_part, '%s_prompt_text' % field)

                if node_type == RelationTemplatePart.TYPE:
                    field_data = relation_data[part_id][field]
                    part_data['%s_object_id' % field] = int(field_data['appellation']['id'])
                    part_data['%s_content_type' % field] = ContentType.objects.get_for_model(Appellation)
                elif node_type == RelationTemplatePart.RELATION:
                    # -vv- Recusion happens here! -vv-
                    child_part = getattr(template_part, '%s_relationtemplate' % field)
                    part_data['%s_object_id' % field], part_data['%s_content_type' % field] = process_recurse(child_part.id, child_part)
                    relation_dependency_graph.add_edge(part_id, part_data['%s_object_id' % field])
                else:   # We will need to create an Appellation.
                    field_data = relation_data[part_id].get(field, None)
                    part_data['%s_object_id' % field] = create_appellation(field_data, template_part, field, evidence_required).id
                    part_data['%s_content_type' % field] = ContentType.objects.get_for_model(Appellation)

            part_data['predicate_id'] = part_data['predicate_object_id']
            del part_data['predicate_object_id']
            del part_data['predicate_content_type']
            part_data['part_of'] = relation_set

            relation = Relation(**part_data)
            relation.save()
            relation_data_processed[part_id] = (relation.id, ContentType.objects.get_for_model(Relation))
            return (relation.id, ContentType.objects.get_for_model(Relation))


        for part_id, template_part in template_parts.iteritems():
            process_recurse(part_id, template_part)

        # The first element should be the root of the graph. This is where we
        #  need to "attach" the temporal relations.
        if len(template_parts) == 1:
            root = template_parts.keys()[0]
        else:
            root = nx.topological_sort(relation_dependency_graph)[0]

        for temporalType in ['start', 'end', 'occur']:
            temporalData = data.get(temporalType, None)
            if temporalData:

                # The predicate indicates the type of temporal dimension.
                predicate_uri = settings.TEMPORAL_PREDICATES.get(temporalType)
                if not predicate_uri:
                    continue
                predicate_concept = Concept.objects.get_or_create(uri=predicate_uri, defaults={'authority': 'Conceptpower'})[0]
                predicate_data = {
                    'occursIn_id': data['occursIn'],
                    'createdBy_id': request.user.id,
                    'interpretation': predicate_concept,
                    'asPredicate': True,
                }
                predicate_appellation = Appellation(**predicate_data)
                predicate_appellation.save()

                # The object need not have a URI (concept) interpretation; we
                #  use an ISO8601 date literal instead. This non-concept
                #  appellation is represented internally as a DateAppellation.
                object_data = {
                    'occursIn_id': data['occursIn'],
                    'createdBy_id': request.user.id,
                }
                for field in ['year', 'month', 'day']:
                    value = temporalData.get(field)
                    if not value:
                        continue
                    object_data[field] = value

                object_appellation = DateAppellation(**object_data)
                object_appellation.save()

                temporalRelation = Relation(**{
                    'source_content_type': ContentType.objects.get_for_model(Relation),
                    'source_object_id': relation_data_processed[root][0],
                    'part_of': relation_set,
                    'predicate': predicate_appellation,
                    'object_content_type': ContentType.objects.get_for_model(DateAppellation),
                    'object_object_id': object_appellation.id,
                    'occursIn_id': data['occursIn'],
                    'createdBy_id': request.user.id,
                })
                temporalRelation.save()

        response_data = {'relationset': relation_set.id}
    else:   # Not sure if we want to do anything for GET requests at this point.
        response_data = {}

    return JsonResponse(response_data)


def network_for_text(request, text_id):
    """
    Provides network data for the graph tab in the text annotation view.
    """
    relationsets = RelationSet.objects.filter(occursIn_id=text_id)
    appellations = Appellation.objects.filter(asPredicate=False,
                                              occursIn_id=text_id)

    # We may want to show this graph on the public (non-annotation) text view,
    #  and thus want to load appellations created by everyone.
    user_id = request.GET.get('user', None)
    if user_id:
        relationsets = relationsets.filter(createdBy_id=user_id)
        appellations = appellations.filter(createdBy_id=user_id)

    nodes, edges = generate_network_data(relationsets, text_id=text_id,
                                         appellation_queryset=appellations)

    return JsonResponse({'elements': nodes.values() + edges.values()})


def generate_network_data(relationset_queryset, text_id=None, user_id=None,
                          appellation_queryset=None):
    """
    Generate a network of :class:`.Concept` instances based on
    :class:.`.RelationSet` instances in ``relationset_queryset``.
    """
    edges = {}
    nodes = {}
    seen = set([])      # Appellation ids.
    # If we want to show any non-related appellations, we can include them
    #  in this separate appellation_queryset.
    if appellation_queryset:
        # Using select_related gathers all of our database queries related to
        #  this queryset into a single call; this is way more performant than
        #  performing queries each time we access a related field.
        related_fields = ['interpretation', 'interpretation__appellation',
                          'interpretation__appellation__occursIn',
                          'interpretation__typed', 'occursIn']
        appellation_queryset = appellation_queryset.filter(asPredicate=False).select_related(*related_fields)

        # Rather than load whole objects, we only load the fields from the
        #  related models that we actually need. This expands the resultset
        #  quite a bit, because we will get a result object for each target of
        #  the furthest downstream M2M relation (Concept.appellation_set in
        #  this case). But it cuts down our database overhead enormously.
        fields = [
            'interpretation__id',  'interpretation__label',
            'interpretation__uri', 'interpretation__description',
            'interpretation__typed__id', 'id',
            'interpretation__appellation__id',
            'interpretation__appellation__occursIn__id',
            'interpretation__appellation__occursIn__title',
            'interpretation__merged_with__id',  'interpretation__merged_with__label',
            'interpretation__merged_with__uri', 'interpretation__merged_with__description',
            'interpretation__merged_with__typed__id',
            'interpretation__merged_with__appellation__id',
            'interpretation__merged_with__appellation__occursIn__id',
            'interpretation__merged_with__appellation__occursIn__title'
        ]

        # This will yield one object per text, so we will see the same
        #  appellation and corresponding interpretations several times.
        for obj in appellation_queryset.values(*fields):
            appell_id = obj.get('id')

            # If the concept used in this appellation has been merged with
            #  another concept, we need to use that master/target concept
            #  instead. In that case, ``merged_with`` will be Truthy. We use
            #  string interpolation below to insert the ``merged_with`` relation
            #  into field lookups. If there is no master/target concept, we will
            #  simply interpolate an empty string.
            if obj.get('interpretation__merged_with__id'):
                mw = 'merged_with__'
            else:
                mw = ''

            # Nodes represent concepts (target of interpretation). We
            #  interpolate ``mw`` in case the concept has been merged.
            node_id = obj.get('interpretation__%sid' % mw)
            node_type = obj.get('interpretation__%styped__id' % mw)
            node_label = obj.get('interpretation__%slabel' % mw)
            node_uri = obj.get('interpretation__%suri' % mw)
            node_description = obj.get('interpretation__%sdescription' % mw)

            if node_id not in nodes:    # Only one node per concept.
                nodes[node_id] = {
                    'data': {
                        'id': node_id,
                        'label': node_label,
                        'uri': node_uri,
                        'description': node_description,
                        'type': node_type,
                        'appellations': set([]),
                        'weight': 1.,
                        'texts': set([])
                    }
                }
            else:   # Don't need to add it again.
                # Node is already in the network, so we just increment weight.
                if appell_id not in seen:   # But only once per appellation.
                    nodes[node_id]['data']['weight'] += 1.
                    seen.add(appell_id)
            # These are useful in the main network view for displaying
            #  information about the texts associated with each concept.
            text_id = obj.get('interpretation__%sappellation__occursIn__id' % mw)
            text_title = obj.get('interpretation__%sappellation__occursIn__title' % mw)

            # We avoid duplicates by using a set; this needs to be recast to
            #  a dict before we return the data.
            nodes[node_id]['data']['texts'].add((text_id, text_title))

            # A set again; must recast to list.
            interp_app_id = obj.get('interpretation__%sappellation__id' % mw)
            nodes[node_id]['data']['appellations'].add(interp_app_id)

    # Rather than load whole objects, we only load the fields from the
    #  related models that we actually need. This expands the resultset
    #  quite a bit, because we will get a result object for each target of
    #  the furthest downstream M2M relation. But it cuts down our database
    #  overhead enormously.
    related_fields = [
        'id', 'occursIn__id', 'occursIn__title',
        'constituents__predicate__interpretation__id',
        'constituents__predicate__interpretation__label',
        'constituents__predicate__interpretation__uri',
        'constituents__predicate__interpretation__description',
        'constituents__predicate__interpretation__merged_with__id',
        'constituents__predicate__interpretation__merged_with__label',
        'constituents__predicate__interpretation__merged_with__uri',
        'constituents__predicate__interpretation__merged_with__description',
        'constituents__source_appellations__id',
        'constituents__object_appellations__id',
        'constituents__source_appellations__asPredicate',
        'constituents__object_appellations__asPredicate',
        'constituents__source_appellations__interpretation__id',
        'constituents__object_appellations__interpretation__id',
        'constituents__source_appellations__interpretation__label',
        'constituents__object_appellations__interpretation__label',
        'constituents__source_appellations__interpretation__uri',
        'constituents__object_appellations__interpretation__uri',
        'constituents__source_appellations__interpretation__description',
        'constituents__object_appellations__interpretation__description',
        'constituents__source_appellations__interpretation__typed__id',
        'constituents__object_appellations__interpretation__typed__id',
        'constituents__source_appellations__interpretation__merged_with__id',
        'constituents__object_appellations__interpretation__merged_with__id',
        'constituents__source_appellations__interpretation__merged_with__label',
        'constituents__object_appellations__interpretation__merged_with__label',
        'constituents__source_appellations__interpretation__merged_with__uri',
        'constituents__object_appellations__interpretation__merged_with__uri',
        'constituents__source_appellations__interpretation__merged_with__description',
        'constituents__object_appellations__interpretation__merged_with__description',
        'constituents__source_appellations__interpretation__merged_with__typed__id',
        'constituents__object_appellations__interpretation__merged_with__typed__id',]

    # We're agnostic about the structure and meaning of the RelationSet, and so
    #  are simply adding edges between any non-predicate concepts that occur
    #  together in a RelationSet. Since we aren't accessing the RelationSet
    #  object directly (only via fields, as described above) we can't get all
    #  of its concepts at once, so we gather them together here in sets. Later
    #  on we iterate over pairs of concepts within each RelationSet using
    #  combinations() to fill in the graph edges.
    relationset_nodes = defaultdict(set)    # Holds Concept (node) ids.

    # Hold on to text ID and title for each RelationSet, so that we can populate
    #  each edge's ``data.texts`` property later on.
    relationset_texts = defaultdict(set)

    # We want to display how each pair of concepts is related. Since we're
    #  agnostic about the structure and meaning of the RelationSet, we simply
    #  gather together all non-generic concepts (i.e. not "be" or "have") used
    #  as "predicates" in the RelationSet. We use the Counter (one per concept)
    #  to keep track of the number of RelationSets that used that predicate for
    #  each pair of concepts.
    relationset_predicates = defaultdict(Counter)

    concept_descriptions = {}   # For ease of access, later.

    # We get one result per constituent Relation in the RelationSet.
    for obj in relationset_queryset.values(*related_fields):
        for field in ['source', 'object']:
            # If the concept used in this appellation has been merged with
            #  another concept, we need to use that master/target concept
            #  instead. In that case, ``merged_with`` will be Truthy. We use
            #  string interpolation below to insert the ``merged_with`` relation
            #  into field lookups.
            if obj.get('constituents__%s_appellations__interpretation__merged_with__id' % field):
                mw = 'merged_with__'
            # If there is no master/target concept, we will simply interpolate
            #  an empty string.
            else:
                mw = ''

            appell_id = obj.get('constituents__%s_appellations__id' % field)
            appell_asPredicate = obj.get('constituents__%s_appellations__asPredicate' % field)
            node_id = obj.get('constituents__%s_appellations__interpretation__%sid' % (field, mw))

            # Node may be a Relation or a DateAppellation, which we don't want
            #  in the network.
            if node_id is None or appell_asPredicate:
                continue

            node_label = obj.get('constituents__%s_appellations__interpretation__%slabel' % (field, mw))
            node_uri = obj.get('constituents__%s_appellations__interpretation__%suri' % (field, mw))
            node_description = obj.get('constituents__%s_appellations__interpretation__%sdescription' % (field, mw))
            node_type = obj.get('constituents__%s_appellations__interpretation__%styped__id' % (field, mw))

            if node_id not in nodes:    # Only one node per concept.
                nodes[node_id] = {
                    'data': {
                        'id': node_id,
                        'label': node_label,
                        'uri': node_uri,
                        'description': node_description,
                        'type': node_type,
                        'appellations': set([]),
                        'weight': 1.,
                        'texts': set([])
                    }
                }
            else:   # Don't need to add it again.
                # Node is already in the network, so we just increment weight.
                if appell_id not in seen:   # But only once per appellation.
                    nodes[node_id]['data']['weight'] += 1.
                    seen.add(appell_id)

            # These are useful in the main network view for displaying
            #  information about the texts associated with each concept.
            text_id = obj.get('occursIn__id')
            text_title = obj.get('occursIn__title')

            # We avoid duplicates by using a set; this needs to be recast to
            #  a dict before we return the data.
            nodes[node_id]['data']['texts'].add((text_id, text_title))

            # A set again; must recast to list.
            interp_app_id = obj.get('constituents__%s_appellations__id' % field)
            nodes[node_id]['data']['appellations'].add(interp_app_id)

        # Check for merged concepts. We'll use string interpolation as before
        #  to select the correct concept.
        #
        # TODO: can we wrap this logic into the block above?
        if obj.get('constituents__source_appellations__interpretation__merged_with__id'):
            source_mw = 'merged_with__'
        else:
            source_mw = ''
        if obj.get('constituents__object_appellations__interpretation__merged_with__id'):
            object_mw = 'merged_with__'
        else:
            object_mw = ''
        if obj.get('constituents__predicate__interpretation__merged_with__id'):
            predicate_mw = 'merged_with__'
        else:
            predicate_mw = ''

        source_id = obj.get('constituents__source_appellations__interpretation__%sid' % source_mw)
        source_asPredicate = obj.get('constituents__source_appellations__asPredicate')
        source_label = obj.get('constituents__source_appellations__interpretation__%slabel' % source_mw)
        source_uri = obj.get('constituents__source_appellations__interpretation__%suri' % source_mw)
        object_id = obj.get('constituents__object_appellations__interpretation__%sid' % object_mw)
        object_asPredicate = obj.get('constituents__object_appellations__asPredicate')
        object_label = obj.get('constituents__object_appellations__interpretation__%slabel' % object_mw)
        object_uri = obj.get('constituents__object_appellations__interpretation__%suri' % object_mw)
        text_id = obj.get('occursIn__id')
        text_title = obj.get('occursIn__title')

        predicate_id = obj.get('constituents__predicate__interpretation__%sid' % predicate_mw)
        predicate_label = obj.get('constituents__predicate__interpretation__%slabel' % predicate_mw)
        predicate_uri = obj.get('constituents__predicate__interpretation__%suri' % predicate_mw)

        relationset_id = obj.get('id')

        if source_id:
            if not source_asPredicate:
                relationset_nodes[relationset_id].add(source_id)
            elif source_uri not in settings.PREDICATES.values():
                concept_descriptions[source_id] = obj.get('constituents__source_appellations__interpretation__%sdescription' % source_mw)
                relationset_predicates[relationset_id][(source_id, source_label)] += 1.

        if object_id:
            if not object_asPredicate:
                relationset_nodes[relationset_id].add(object_id)
            elif object_uri not in settings.PREDICATES.values():
                concept_descriptions[object_id] = obj.get('constituents__object_appellations__interpretation__%sdescription' % object_mw)
                relationset_predicates[relationset_id][(object_id, object_label)] += 1.

        if predicate_id and predicate_uri not in settings.PREDICATES.values():
            concept_descriptions[predicate_id] = obj.get('constituents__predicate__interpretation__%sdescription' % predicate_mw)
            relationset_predicates[relationset_id][(predicate_id, predicate_label)] += 1

        relationset_texts[relationset_id] = (text_id, text_title)

    for relationset_id, relation_nodes in relationset_nodes.iteritems():
        for source_id, object_id in combinations(relation_nodes, 2):
            edge_key = tuple(sorted((source_id, object_id)))
            if edge_key not in edges:
                edges[edge_key] = {
                    'data': {
                        'id': len(edges),
                        'source': source_id,
                        'target': object_id,
                        'weight': 0.,
                        'texts': set([]),
                        'relations': Counter(),
                    }
                }
            edges[edge_key]['data']['texts'].add(relationset_texts[relationset_id])
            for key, value in relationset_predicates[relationset_id].items():
                edges[edge_key]['data']['relations'][key] += value
            edges[edge_key]['data']['weight'] += 1.


    for node in nodes.values():
        node['data']['texts'] = [{'id': text[0], 'title': text[1]}
                                  for text in list(node['data']['texts'])]
        node['data']['appellations'] = list(node['data']['appellations'])


    for edge in edges.values():
        edge['data']['texts'] = [{'id': text[0], 'title': text[1]}
                                  for text in list(edge['data']['texts'])]
        edge['data']['relations'] = [{
            'concept_id': relkey[0],
            'concept_label': relkey[1],
            'count': count,
            'description': concept_descriptions[relkey[0]],
        } for relkey, count in edge['data']['relations'].items()]

    return nodes, edges


@login_required
def sign_s3(request):
    """
    Genaration of a temporary signtaure using AWS secret key and access key.
    https://devcenter.heroku.com/articles/s3-upload-python

    This is used for user profile images.
    """

    if request.method == 'GET':
        AWS_ACCESS_KEY = settings.AWS_ACCESS_KEY
        AWS_SECRET_KEY = settings.AWS_SECRET_KEY
        S3_BUCKET = settings.S3_BUCKET

        object_name = urllib.quote_plus(request.GET.get('file_name'))
        mime_type = request.GET.get('file_type')

        secondsPerDay = 24*60*60
        expires = int(time.time()+secondsPerDay)
        amz_headers = "x-amz-acl:public-read"

        string_to_sign = "PUT\n\n%s\n%d\n%s\n/%s/%s" % (mime_type, expires, amz_headers, S3_BUCKET, object_name)

        encodedSecretKey = AWS_SECRET_KEY.encode()
        encodedString = string_to_sign.encode()
        h = hmac.new(encodedSecretKey, encodedString, sha1)
        hDigest = h.digest()
        signature = base64.b64encode(hDigest).strip()
        signature = urllib.quote_plus(signature)
        url = 'https://%s.s3.amazonaws.com/%s' % (S3_BUCKET, object_name)

        # TODO: can we use the built-in Django JsonResponse for this?
        return JsonResponse({
            'signed_request': '%s?AWSAccessKeyId=%s&Expires=%s&Signature=%s' % (url, AWS_ACCESS_KEY, expires, signature),
            'url': url,
        })


def concept_autocomplete(request):
    """
    Provides the :class:`.Concept` autocomplete in the home view.
    """
    query = request.GET.get('q', '')

    if not query:
        suggestions = []
    else:
        sqs = SearchQuerySet().models(Concept).filter(label__icontains=query.lower())[:20]
        suggestions = [{
            'label': result.label.title(),
            'id': result.id,
            'type': result.typed,
            'description': result.description,
            'uri': result.uri
        } for result in sqs]

    # TODO: can we use the built-in Django JsonResponse for this?
    response_data = json.dumps({'results': suggestions})
    return HttpResponse(response_data, content_type='application/json')



def appellation_xml(request, appellation_id):
    """
    Return partial quad-xml for an :class:`.Appellation`\.
    """
    appellation = Appellation.objects.get(pk=appellation_id)
    appellation_xml = quadriga.to_appellationevent(appellation, toString=True)
    return HttpResponse(appellation_xml, content_type='application/xml')


def relation_xml(request, relation_id):
    """
    Return partial quad-xml for an :class:`.Appellation`\.
    """
    relation = Relation.objects.get(pk=relation_id)
    relation_xml = quadriga.to_relationevent(relation, toString=True)
    return HttpResponse(relation_xml, content_type='application/xml')


def relationset_xml(request, relationset_id):
    """
    Return partial quad-xml for an :class:`.Appellation`\.
    """
    relationset = RelationSet.objects.get(pk=relationset_id)
    relation_xml = quadriga.to_relationevent(relationset.root, toString=True)
    return HttpResponse(relation_xml, content_type='application/xml')


def text_xml(request, text_id, user_id):
    text = Text.objects.get(pk=text_id)
    user = VogonUser.objects.get(pk=user_id)
    relationsets = RelationSet.objects.filter(occursIn_id=text_id, createdBy_id=user_id)
    text_xml = quadriga.to_quadruples(relationsets, text, user, toString=True)
    # r = quadriga.submit_relationsets(relationsets, text, user)
    return HttpResponse(text_xml, content_type='application/xml')


@login_required
def repository_collections(request, repository_id):
    template = loader.get_template('annotations/repository_collections.html')
    repository = get_object_or_404(Repository, pk=repository_id)

    context = RequestContext(request, {
        'user': request.user,
        'repository': repository,
        'title': 'Browse collections in %s' % repository.name,
    })

    return HttpResponse(template.render(context))


@login_required
def repository_collection(request, repository_id, collection_id):
    template = loader.get_template('annotations/repository_collection.html')
    repository = get_object_or_404(Repository, pk=repository_id)
    collection = repository.collection(id=collection_id)

    context = RequestContext(request, {
        'user': request.user,
        'repository': repository,
        'collection': collection,
        'title': 'Browse collections in %s' % repository.name,
    })

    return HttpResponse(template.render(context))


@login_required
def repository_browse(request, repository_id):
    template = loader.get_template('annotations/repository_browse.html')
    repository = get_object_or_404(Repository, pk=repository_id)

    context = RequestContext(request, {
        'user': request.user,
        'repository': repository,
        'title': 'Browse repository %s' % repository.name,
    })

    return HttpResponse(template.render(context))


@login_required
def repository_search(request, repository_id):
    template = loader.get_template('annotations/repository_search.html')
    repository = get_object_or_404(Repository, pk=repository_id)
    query = request.GET.get('query', None)
    if query:
        results = repository.search(search=query)
        form = RepositorySearchForm({'query': query})
    else:
        results = None
        form = RepositorySearchForm()

    context = RequestContext(request, {
        'user': request.user,
        'repository': repository,
        'title': 'Browse repository %s' % repository.name,
        'form': form,
        'results': results,
        'query': query,
    })

    return HttpResponse(template.render(context))


@login_required
def repository_details(request, repository_id):
    template = loader.get_template('annotations/repository_details.html')
    repository = get_object_or_404(Repository, pk=repository_id)


    context = RequestContext(request, {
        'user': request.user,
        'repository': repository,
        'title': 'Repository details: %s' % repository.name,

    })

    return HttpResponse(template.render(context))


@login_required
def repository_list(request):
    template = loader.get_template('annotations/repository_list.html')
    repositories = Repository.objects.all()

    context = RequestContext(request, {
        'user': request.user,
        'repositories': repositories,
        'title': 'Repositories',

    })

    return HttpResponse(template.render(context))


@login_required
def repository_text(request, repository_id, text_id):
    repository = get_object_or_404(Repository, pk=repository_id)
    result = repository.read(id=int(text_id))

    defaults = {
        'title': getattr(result.get('title'), 'value', None),
        'created': getattr(result.get('created'), 'value', None),
        #'source': repository,
        'addedBy': request.user,
        'originalResource': getattr(result.get('url'), 'value', None),
    }
    text, _ = Text.objects.get_or_create(uri=result.uri.value, defaults=defaults)
    return HttpResponseRedirect(reverse('text', args=(text.id,)))
