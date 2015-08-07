from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework import viewsets, exceptions
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from concepts.models import Concept
from concepts.authorities import search
from models import *
from forms import CrispyUserChangeForm
from serializers import *

import hashlib
from itertools import chain

def user_texts(user):
    return Text.objects.filter(relation__createdBy__pk=user.id).distinct()

@login_required
def add_text(request):
    """
    Select a new Text from a Repository, and make it available for annotation.
    """
    template = loader.get_template('annotations/add_text.html')
    context = RequestContext(request, {
        'user': request.user,
        'texts': user_texts(request.user)
    })
    return HttpResponse(template.render(context))

@login_required
def settings(request):
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
    })
    return HttpResponse(template.render(context))


@login_required
def dashboard(request):
    template = loader.get_template('annotations/dashboard.html')
    context = RequestContext(request, {
        'user': request.user,
        'texts': user_texts(request.user)
    })
    return HttpResponse(template.render(context))


@ensure_csrf_cookie
@login_required
def text(request, textid):
    template = loader.get_template('annotations/text.html')
    text = get_object_or_404(Text, pk=textid)
    context = RequestContext(request, {
        'textid': textid,
        'text': text,
        'userid': request.user.id,
		'title': 'Annotate Text',
    })
    return HttpResponse(template.render(context))


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
