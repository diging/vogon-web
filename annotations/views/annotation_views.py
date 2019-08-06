from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse

from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie

from annotations.models import Relation, Appellation, VogonUser, Text, RelationSet
from annotations.annotators import annotator_factory

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from urllib.parse import urlencode
@login_required
@ensure_csrf_cookie
def annotate(request, text_id):
    text = get_object_or_404(Text, pk=text_id)
    annotator = annotator_factory(request, text)
    return annotator.render()


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

    context = {
        'paginator': paginator,
        'relations': relations,
        'params': request.GET.urlencode(),
        'filter': filtered,
        'params_data': urlencode(params_data),
        }
    return render(request, 'annotations/relations.html', context)


def relations_graph(request):
    from annotations.filters import RelationSetFilter
    from annotations.views.network_views import generate_network_data_fast
    qs = RelationSet.objects.all()
    filtered = RelationSetFilter(request.GET, queryset=qs)
    qs = filtered.qs

    if request.GET.get('mode', None) == 'data':

        nodes, edges = generate_network_data_fast(qs)
        return JsonResponse({'elements': list(nodes.values()) + list(edges.values())})

    context = {
        'relations': relations,
        'filter': filtered,
        'data_path': request.path + '?' + request.GET.urlencode() + '&mode=data',
        'params': request.GET.urlencode(),
    }

    return render(request, 'annotations/relations_graph.html', context)
