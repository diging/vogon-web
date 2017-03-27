from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from django.core.urlresolvers import reverse
from concepts.models import Concept, Type
from concepts.filters import *
from annotations.models import RelationSet, Appellation
from django.shortcuts import render, get_object_or_404
from concepts.authorities import ConceptpowerAuthority, update_instance
import re
import string
from unidecode import unidecode


def _find_similar(concept):
    def _to_concept(datum):
        try:
            return Concept.objects.get(uri=datum.get('id'))
        except Concept.DoesNotExist:
            typed_uri = datum.get('type_id')
            if typed_uri:
                typed = Type.objects.get_or_create(uri=typed_uri)[0]
            else:
                typed = None
            return Concept.objects.create(
                label = datum.get('lemma'),
                pos = datum.get('pos'),
                typed = typed,
                authority = 'Conceptpower',
                uri = datum.get('id'),
                description = datum.get('description'),
                concept_state = Concept.RESOLVED,
            )
    # Look for similar concepts that already exist, to avoid stupid mistakes.
    manager = ConceptpowerAuthority()
    q = re.sub("[0-9]", "", unidecode(concept.label).translate(None, string.punctuation).lower())
    candidates = []
    if q:    # TODO: conceptpower-api should have some custom exceptions to catch.
        candidates += map(_to_concept, manager.search(q))
    matches = []
    if concept.uri:
        _data = manager.search(equal_to=concept.uri)

        if _data:
            matches += map(_to_concept, _data)
    return candidates, matches


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
    next_page = request.GET.get('next', reverse('concepts'))

    context = {
        'concept': concept,
        'next_page': next_page,
    }

    # TODO: say something more informative.
    if concept.concept_state != Concept.PENDING:
        return HttpResponseRedirect(next_page)

    if request.GET.get('confirmed', False):
        concept.concept_state = Concept.APPROVED
        concept.save()
        return HttpResponseRedirect(next_page)

    candidates, matches = _find_similar(concept)

    context.update({
        'candidates': candidates,
        'matches': matches,
    })
    return render(request, 'annotations/concept_approve.html', context)


@staff_member_required
def resolve_concept(request, concept_id):
    """
    Attempt to resolve a concept.
    """
    from concepts.authorities import resolve
    concept = get_object_or_404(Concept, pk=concept_id)
    next_page = request.GET.get('next', reverse('concepts'))

    context = {
        'concept': concept,
        'next_page': next_page
    }

    # Don't bother trying to resolve a non-pending Concept.
    if concept.concept_state != Concept.PENDING:
        return HttpResponseRedirect(next_page)

    try:
        result = resolve(Concept, concept)
    except Exception as E:
        context.update({
            'exception': str(E)
        })
        return render(request, 'annotations/concept_resolve.html', context)
    if not result:
        return render(request, 'annotations/concept_resolve.html', context)

    return HttpResponseRedirect(next_page)


@staff_member_required
def merge_concepts(request, source_concept_id, target_concept_id):
    source = get_object_or_404(Concept, pk=source_concept_id)
    target = get_object_or_404(Concept, pk=target_concept_id)

    next_page = request.GET.get('next', reverse('concepts'))

    source.concept_state = Concept.MERGED
    source.merged_with = target
    source.save()

    # It may be the case that other concepts have been merged into these
    #  unresolved concepts. Therefore, we recursively collect all of
    #  these "child" concepts, and point them to the master concept.
    children_queryset = Concept.objects.filter(pk__in=source.children)
    children_queryset.update(merged_with=target)
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
        'path': request.path + '?' + request.GET.urlencode(),
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
    from concepts.authorities import add
    concept = get_object_or_404(Concept, pk=concept_id)
    next_page = request.GET.get('next', reverse('concepts'))
    context = {
        'concept': concept,
        'next_page': next_page,
    }
    if concept.concept_state != Concept.APPROVED:
        return HttpResponseRedirect(next_page)

    if request.GET.get('confirmed', False):
        response_data = add(concept)
        concept.uri = response_data['uri']
        concept.authority = 'Conceptpower'
        concept.concept_state = Concept.RESOLVED
        concept.save()
        return HttpResponseRedirect(next_page)

    candidates, matches = _find_similar(concept)

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
        'next_page': next_page,
    }
    return render(request, "annotations/concept_edit.html", context)
