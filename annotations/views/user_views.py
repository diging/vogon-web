"""
Provides user-oriented views, including dashboard, registration, etc.
"""

from django.conf import settings
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import RequestContext, loader
from django.views.decorators.csrf import csrf_protect

# TODO: should we be using VogonGroup?
from django.contrib.auth.models import Group

from annotations.models import (VogonUser, Text, Appellation, RelationSet,
                                TextCollection, Relation)
from annotations.forms import RegistrationForm, UserChangeForm
from annotations.display_helpers import (user_recent_texts,
                                         get_recent_annotations)

import datetime
from isoweek import Week


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
            # TODO: check uniqueness?
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
            redirect_target = reverse('user_details', args=[request.user.id])
            return HttpResponseRedirect(redirect_target)
    else:
        form = UserChangeForm(instance=request.user)
        # Assign default image in the preview if no profile image is selected
        #  for the user.
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

    flds = ['id', 'name', 'description']
    projects_owned = request.user.collections.all().values_list(*flds)
    projects_contributed = request.user.contributes_to.all().values_list(*flds)

    appellation_qs = Appellation.objects.filter(createdBy__pk=request.user.id)\
                                        .filter(asPredicate=False)\
                                        .distinct().count()
    relationset_qs = RelationSet.objects.filter(createdBy__pk=request.user.id)\
                                        .distinct().count()

    context = RequestContext(request, {
        'title': 'Dashboard',
        'user': request.user,
        'recent_texts': recent_texts[:5],
        'added_texts': added_texts[:5],
        'projects_owned': projects_owned[:5],
        'projects_contributed': projects_contributed[:5],
        'appellationCount': appellation_qs,
        'relation_count': relationset_qs,
    })
    return HttpResponse(template.render(context))


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
            'recent_activity': get_recent_annotations(user=user),
            'projects': projects,
        })
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
    queryset = VogonUser.objects.exclude(id=-1).order_by(sort)

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
