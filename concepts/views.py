from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from django.core.urlresolvers import reverse
from concepts.models import Concept, Type
from concepts.filters import *
from concepts.lifecycle import *
from annotations.models import RelationSet, Appellation, TextCollection, VogonUserDefaultProject
from django.shortcuts import render, get_object_or_404
from concepts.authorities import ConceptpowerAuthority, update_instance
from django.contrib.auth.decorators import login_required
import re, urllib, string
from unidecode import unidecode




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
        'next_page': urllib.quote_plus(next_page),
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
        'path': urllib.quote_plus(request.path + '?' + request.GET.urlencode()),
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
    context = {
        'concept': concept,
        'next_page': urllib.quote_plus(next_page),
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
        'next_page': urllib.quote_plus(next_page),
    }
    return render(request, "annotations/concept_edit.html", context)



@login_required
def sandbox(request, text_id):
    from annotations.models import Text
    text = Text.objects.get(pk=text_id)
    project_id = request.GET.get('project')
    if project_id:
        project = TextCollection.objects.get(pk=project_id)
    else:

        project = TextCollection.objects.filter(is_default_for__for_user=request.user).first()
        if project is None:
            project = TextCollection.objects.create(
                name="%s's default collection" % request.user.username,
                ownedBy=request.user)
            VogonUserDefaultProject.objects.create(for_user=request.user, project=project)

    project.texts.add(text)

    context = {
        'text': text,
        'project': project,
        'user': request.user
    }
    return render(request, "annotations/vue.html", context)
