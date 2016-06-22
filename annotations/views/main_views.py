"""
Top-level views.
"""

from django.http import HttpResponse
from django.template import RequestContext, loader
from django.db.models.expressions import DateTime

from annotations.models import Relation, Appellation, VogonUser, Text
from annotations.display_helpers import get_recent_annotations

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
        'recent_combination': get_recent_annotations(last=10),
        'title': 'Build the epistemic web'
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
    recent_texts = Text.objects.annotate(hour=DateTime("added", "hour", pytz.timezone("UTC")))\
                               .values("hour", "addedBy__username")\
                               .annotate(created_count=Count('id'))\
                               .order_by("-hour", "addedBy")

    context = {
        'recent_texts': recent_texts,
        'recent_combination': get_recent_annotations()
    }
    return HttpResponse(template.render(context))
