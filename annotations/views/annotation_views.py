import json
import itertools as it
from urllib.parse import urlencode
from requests import Response
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.core import serializers
from django_filters import FilterSet
from django_filters.rest_framework import DjangoFilterBackend
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework import viewsets
from rest_framework.response import Response as RestResponse
from rest_framework.decorators import api_view, action

from annotations.models import Relation, Appellation, VogonUser, Text, RelationSet, TextCollection, Repository, Appellation
from annotations.annotators import annotator_factory
from annotations.serializers import (RelationSerializer, RelationSetSerializer,
    ProjectSerializer, UserSerializer, Text2Serializer)
from annotations.filters import RelationSetFilter
from annotations.tasks import submit_relationsets_to_quadriga


class RelationSetViewSet(viewsets.ModelViewSet):
    queryset = RelationSet.objects.all().order_by('-created')
    serializer_class = RelationSetSerializer

    def list(self, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer_class()

        self.page = self.paginate_queryset(queryset)
        if self.page is not None:
            serializer = self.get_serializer(self.page, many=True)
            return self.get_paginated_response(serializer.data, meta=self.request.query_params.get('meta', False))
        else:
            relations = serializer(queryset, many=True).data
            
        return RestResponse(relations)

    def get_paginated_response(self, data, meta):
        extra = {}
        if meta:
            projects = TextCollection.objects.all()
            users = VogonUser.objects.all()
            extra = {
                'projects': ProjectSerializer(projects, many=True).data,
                'users': UserSerializer(users, many=True).data
            }
        return RestResponse({
            'count':len(self.get_queryset()),
            'results': data,
            **extra
        })
    
    def get_queryset(self, *args, **kwargs):
        queryset = super(RelationSetViewSet, self).get_queryset(*args, **kwargs)
        filtered = RelationSetFilter(self.request.query_params, queryset)
        return filtered.qs

    @action(detail=False, methods=['post'])
    def submit_for_quadriga(self, request):
        relationset_ids = request.data.get('relationset_ids', [])
        relationsets = RelationSet.objects.filter(
            pk__in=relationset_ids,
            createdBy=request.user,
            submitted=False,
        )
        relationsets = [x for x in relationsets if x.ready()]
        
        project_grouper = lambda x: getattr(x.project, 'quadriga_id', -1)
        for project_id, project_group in it.groupby(relationsets, key=project_grouper):
            for text_id, text_group in it.groupby(project_group, key=lambda x: x.occursIn.id):
                text = Text.objects.get(pk=text_id)
                rsets = []
                for rs in text_group:
                    rsets.append(rs.id)
                    rs.save()
                kwargs = {}
                if project_id:
                    kwargs.update({
                        'project_id': project_id
                    })

                submit_relationsets_to_quadriga(rsets, text.id, request.user.id, **kwargs)


        return RestResponse({})

#@login_required
#@ensure_csrf_cookie
@api_view(['GET', 'POST'])
def annotate(request, text_id):
    text = get_object_or_404(Text, pk=text_id)
    annotator = annotator_factory(request, text)
    data = annotator.render()
    appellations = Appellation.objects.filter(occursIn=text.id)
    content = data['content'].decode("utf-8")
    data['content'] = content
    project = TextCollection.objects.get(id=data['project'])
    data['project'] = project
    data['appellations'] = appellations
    print(appellations)
    data['relations'] = Relation.objects.filter(occursIn=text.id)
    relationsets = RelationSet.objects.filter(
        occursIn=text.id, 
        createdBy=request.user, 
        submitted=False,
    )
    relationsets = [x for x in relationsets if x.ready()]
    data['pending_relationsets'] = relationsets
    serializer = Text2Serializer(data, context={'request': request})
    return RestResponse(serializer.data)


@login_required
def annotation_display(request, text_id):
    text = get_object_or_404(Text, pk=text_id)
    annotator = annotator_factory(request, text)
    return annotator.render_display()

@login_required
def annotate_image(request, text_id):
    template = "annotations/annotate_image.html"
    text = Text.objects.get(pk=text_id)

    return render(request, template, context)


def relations(request):
    from annotations.filters import RelationSetFilter


    filtered = RelationSetFilter(request.GET, queryset=RelationSet.objects.all())
    qs = filtered.qs

    paginator = Paginator(qs, 40)
    page = request.GET.get('page')

    data = filtered.form.cleaned_data
    params_data = {}
    for key, value in list(data.items()):
        if key in ('createdBy', 'project'):
            if value is not None and hasattr(value, 'id'):
                params_data[key] = value.id
        elif key in ('createdAfter', 'createdBefore'):
            if value is not None:
                value = '{0.month}/{0.day}/{0.year}'.format(value)
                params_data[key] = value
        else:
            params_data[key] = value


    try:
        relations = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        relations = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        relations = paginator.page(paginator.num_pages)
    count = paginator.count
    previous = None if not relations.has_previous() else relations.previous_page_number()
    next =None if not relations.has_next() else relations.next_page_number()
    relationsserializer = RelationSerializer(relations, many=True)
    context = {
        'paginator': {
            'count':count,
            'previous':previous,
            'next':next
        },
        'relations': relationsserializer.data,
        'params': request.GET.urlencode(),
        'filter': filtered.data,
        'params_data': urlencode(params_data),
        }
    return Response(json.dumps(context), content_type='application/json')


def relations_graph(request):
    from annotations.filters import RelationSetFilter
    from annotations.views.network_views import generate_network_data_fast
    qs = RelationSet.objects.all()
    filtered = RelationSetFilter(request.GET, queryset=qs)
    qs = filtered.qs

    if request.GET.get('mode', None) == 'data':

        nodes, edges = generate_network_data_fast(qs)
        return JsonResponse({'elements': list(nodes.values()) + list(edges.values())})
    # relationsserializer = RelationSerializer(relations, many=True)
    relationsvalue= relations(request)
    context = {
        'relations': relationsvalue.json(),
        'filter': filtered.data,
        'data_path': request.path + '?' + request.GET.urlencode() + '&mode=data',
        'params': request.GET.urlencode(),
    }

    return HttpResponse(json.dumps(context), content_type='application/json')
