"""
Top-level views.
"""

from django.http import HttpResponse
from django.shortcuts import render
from annotations.models import Relation, Appellation, VogonUser, Text, RelationSet
# from annotations.display_helpers import get_recent_annotations

import pytz


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
    template = "annotations/home.html"
    user_count = VogonUser.objects.filter(is_active=True).count()
    text_count = Text.objects.all().count()
    appellation_count = Appellation.objects.count()
    relation_count = Relation.objects.count()
    context = {
        'user_count': user_count,
        'text_count': text_count,
        'relation_count': relation_count,
        'appellation_count': appellation_count,
        # 'recent_combination': get_recent_annotations(last=10),
        'title': 'Build the epistemic web',
        'relations': RelationSet.objects.all().order_by('-created')[:10]
    }
    return render(request, template, context)


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
    template = "annotations/about.html"
    context = {}
    context.update({
        'title': 'About VogonWeb'
    })
    return render(request, template, context)


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
    template = "annotations/recent_activity.html"
    # recent_texts = Text.objects.annotate(hour=DateTime("added", "hour", pytz.timezone("UTC")))\
    #                            .values("hour", "addedBy__username")\
    #                            .annotate(created_count=Count('id'))\
    #                            .order_by("-hour", "addedBy")

    context = {
        'recent_texts': [],
        # 'recent_combination': get_recent_annotations()
    }
    return render(request, template, context)
