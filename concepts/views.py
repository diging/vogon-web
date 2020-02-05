from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
import re, urllib.request, urllib.parse, urllib.error, string
from unidecode import unidecode
from urllib.parse import urlencode
import uuid

from annotations.models import RelationSet, Appellation, TextCollection, VogonUserDefaultProject
from annotations.serializers import (
    ConceptSerializer, TypeSerializer, RelationSetSerializer,
    ConceptLifecycleSerializer, ConceptExampleSerializer
)
from concepts.models import Concept, Type
from concepts.filters import *
from concepts.lifecycle import *
from concepts.authorities import ConceptpowerAuthority, update_instance
from goat.views import search as search_concepts


class ConceptViewSet(viewsets.ModelViewSet):
    queryset = Concept.objects.filter(~Q(concept_state=Concept.REJECTED)) \
            .filter(appellation__isnull=False) \
            .distinct('id').order_by('-id')
    serializer_class = ConceptSerializer

    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()
        concept = get_object_or_404(queryset, pk=pk)
        serializer = self.get_serializer(concept, many=False)
        result = serializer.data
        relations = RelationSet.objects.filter(
            terminal_nodes=concept
        ).order_by('-created')[:10]
        relations = RelationSetSerializer(relations, many=True, context={'request': request})
        result['relations'] = relations.data

        types = Type.objects.all()
        result['types'] = TypeSerializer(types, many=True, context={'request': request}).data

        return Response(result)

    def create(self, request, *args, **kwargs):
        data = request.data
        if data['uri'] == 'generate':
            data['uri'] = 'http://vogonweb.net/{0}'.format(uuid.uuid4())

        if 'lemma' not in data:
            data['lemma'] = data['label']

        concept_type = data.get('typed', '')
        try:
            int(concept_type)
        except:
            data['typed'] = Type.objects.get(uri=concept_type).id

        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as E:
            raise E

        self.perform_create(serializer)
        headers = self.get_success_headers(data)
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED,
                        headers=headers)

    def get_queryset(self, *args, **kwargs):
        """
        Filter by part of speech (`pos`).
        """
        queryset = super(ConceptViewSet, self).get_queryset(*args, **kwargs)
        
        # Limit results to those with ``pos``.
        pos = self.request.query_params.get('pos', None)
        if pos:
            if pos != 'all':
                queryset = queryset.filter(pos__in=[pos.upper(), pos.lower()])

        # Search Concept labels for ``search`` param.
        query = self.request.query_params.get('search', None)
        authority = self.request.query_params.get('authority', None)
        remote = self.request.query_params.get('remote', False)
        uri = self.request.query_params.get('uri', None)
        type_id = self.request.query_params.get('typed', None)
        type_strict = self.request.query_params.get('strict', None)
        type_uri = self.request.query_params.get('type_uri', None)
        max_results = self.request.query_params.get('max', None)
        concept_state = self.request.query_params.get('concept_state', None)

        if uri:
            queryset = queryset.filter(uri=uri)
        if authority:
            queryset = queryset.filter(authority=authority)
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

            queryset = queryset.filter(label__icontains=query)

        if max_results:
            return queryset[:max_results]
        if concept_state:
            queryset = queryset.filter(concept_state=concept_state)
        return queryset

    @action(detail=False)
    def search(self, request):
        q = request.query_params.get('q')
        pos = request.query_params.get('pos')
        force = request.query_params.get('force')
        if not q:
            return Response({'results': []})

        concepts = search_concepts(q=q, user_id=request.user.id, pos=pos, limit=50, force=force)

        def _relabel(datum):
            _fields = {
                'name': 'label',
                'id': 'alt_id',
                'identifier': 'uri'
            }
            return {_fields.get(k, k): v for k, v in list(datum.items())}

        return Response({'results': list(map(_relabel, concepts))})

    @action(detail=True, methods=['GET'])
    def matches(self, request, pk=None):
        concept = get_object_or_404(Concept, pk=pk)
        manager = ConceptLifecycle(concept)

        candidates = manager.get_similar()
        matches = manager.get_matching()

        return Response({
            'concept': self.get_serializer(concept, many=False).data,
            'candidates': ConceptLifecycleSerializer(candidates, many=True).data,
            'matches': ConceptLifecycleSerializer(matches, many=True).data,
        })
    
    @action(detail=True, methods=['POST'])
    def approve(self, request, pk=None):
        concept = get_object_or_404(Concept, pk=pk)
        manager = ConceptLifecycle(concept)
        manager.approve()
        
        return Response({
            'success': True
        })

    @action(detail=True, methods=['POST'])
    def merge(self, request, pk=None):
        source = get_object_or_404(Concept, pk=pk)
        manager = ConceptLifecycle(source)

        target = request.query_params.get('target')
        manager.merge_with(target)

        return Response({
            'success': True
        })

    @action(detail=True, methods=['POST'])
    def add(self, request, pk=None):
        concept = get_object_or_404(Concept, pk=pk)
        manager = ConceptLifecycle(concept)

        if concept.concept_state != Concept.APPROVED:
            return Response({
                'success': False,
                'error': 'Concept should be approved!'
            }, status=403)

        try:
            manager.add()
        except ConceptUpstreamException as E:
            return Response({
                'success': False,
                'error': 'Conceptpower is causing problems - %s' % str(E)
            }, status=500)
        except ConceptLifecycleException as E:
            return Response({
                'success': False,
                'error': 'Conceptpower lifecycle error - %s' % str(E)
            }, status=500)

        return Response({
            'success': True
        })


class ConceptTypeViewSet(viewsets.ModelViewSet):
    queryset = Type.objects.all()
    serializer_class = TypeSerializer
    pagination_class = None

    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()
        concept_type = get_object_or_404(queryset, pk=pk)
        serializer = self.get_serializer(concept_type, many=False)
        result = serializer.data
        
        examples = Concept.objects.filter(
            typed__id=pk,
            concept_state=Concept.RESOLVED
        ).values('id', 'label', 'description')[:20]
        
        result['examples'] = ConceptExampleSerializer(
            examples, many=True, partial=True,
            context={'request': request}
        ).data
        return Response(result)

def list_concept_types(request):
    """
    List all of the concept types
    """
    types = Type.objects.all().values('label', 'description', 'id')
    # types = Concept.objects.exclude(typed__isnull=True).values('typed__label','typed').distinct()

    template = "annotations/concept_types.html"
    context = {
        'types': types,
        'user': request.user,
    }
    return render(request, template, context)


def type(request, type_id):
    """
    Fetch description about type
    """
    instance = Type.objects.get(pk=type_id)

    examples  = Concept.objects.filter(typed__id=type_id, concept_state=Concept.RESOLVED).values('id', 'label', 'description')
    template = "annotations/concept_type_detail.html"
    context = {
        'type': instance,
        'user': request.user,
        'examples': examples[:20],
    }
    return render(request, template, context)


@staff_member_required
def approve_concept(request, concept_id):
    """

    """

    concept = get_object_or_404(Concept, pk=concept_id)
    manager = ConceptLifecycle(concept)
    next_page = request.GET.get('next', reverse('concepts'))

    context = {
        'concept': concept,
        'next_page': urllib.parse.quote_plus(next_page),
    }

    # TODO: say something more informative.
    if concept.concept_state != Concept.PENDING:
        return HttpResponseRedirect(next_page)

    if request.GET.get('confirmed', False):
        manager.approve()
        return HttpResponseRedirect(next_page)

    candidates = manager.get_similar()
    matches = manager.get_matching()

    context.update({
        'candidates': candidates,
        'matches': matches,
    })
    return render(request, 'annotations/concept_approve.html', context)


@staff_member_required
def merge_concepts(request, source_concept_id):
    source = get_object_or_404(Concept, pk=source_concept_id)
    manager = ConceptLifecycle(source)
    target_uri = request.GET.get('target')
    manager.merge_with(target_uri)

    next_page = request.GET.get('next', reverse('concepts'))

    return HttpResponseRedirect(next_page)


def concepts(request):
    """
    List all concepts.
    """
    qs = Concept.objects.filter(appellation__isnull=False).distinct('id').order_by('-id')

    filtered = ConceptFilter(request.GET, queryset=qs)
    qs = filtered.qs

    paginator = Paginator(qs, 20)
    page = request.GET.get('page')

    data = filtered.form.cleaned_data
    params_data = {}
    for key, value in list(data.items()):
        if key in ('typed'):
           if value is not None and hasattr(value, 'id'):
               params_data[key] = value.id
        elif value is not None:
            params_data[key] = value

    try:
        concepts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        concepts = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        concepts = paginator.page(paginator.num_pages)

    context = {
        'paginator': paginator,
        'concepts': concepts,
        'filter': filtered,
        'path': urllib.parse.quote_plus(request.path + '?' + request.GET.urlencode()),
        'params_data': urlencode(params_data),
    }

    return render(request, 'annotations/concepts.html', context)


def concept(request, concept_id):
    """
    Details about a :class:`.Concept`\, including its associated annotations.
    """

    concept = get_object_or_404(Concept, pk=concept_id)
    context = {
        'concept': concept,
        'relations': RelationSet.objects.filter(terminal_nodes=concept).order_by('-created')[:10]
    }
    return render(request, "annotations/concept_details.html", context)



@staff_member_required
def add_concept(request, concept_id):

    concept = get_object_or_404(Concept, pk=concept_id)
    manager = ConceptLifecycle(concept)
    next_page = request.GET.get('next', reverse('concepts'))
    back_to_page = request.GET.get('next')
    context = {
        'concept': concept,
        'next_page': urllib.parse.quote_plus(next_page),
        'back_to_page': back_to_page
    }
    if concept.concept_state != Concept.APPROVED:
        return HttpResponseRedirect(next_page)

    if request.GET.get('confirmed', False):
        try:
            manager.add()
        except ConceptUpstreamException as E:
            return HttpResponse("Conceptpower is causing all kinds of problems"
                                " right now: %s" % str(E), status=500)
        return HttpResponseRedirect(next_page)


    candidates = manager.get_similar()
    matches = manager.get_matching()

    context.update({
        'candidates': candidates,
        'matches': matches,
    })

    return render(request, "annotations/concept_add.html", context)


@staff_member_required
def edit_concept(request, concept_id):
    from concepts.forms import ConceptForm

    concept = get_object_or_404(Concept, pk=concept_id)
    next_page = request.GET.get('next', reverse('concept', args=(concept_id,)))

    if request.method == 'POST':
        form = ConceptForm(request.POST, instance=concept)
        if form.is_valid():
            form.save()
        return HttpResponseRedirect(next_page)
    if request.method == 'GET':
        form = ConceptForm(instance=concept)
    context = {
        'form': form,
        'concept': concept,
        'next_page': urllib.parse.quote_plus(next_page),
    }
    return render(request, "annotations/concept_edit.html", context)



@login_required
def sandbox(request, text_id):
    from annotations.models import RelationTemplate

    return render(request, "annotations/relationtemplate_creator.html", {})
