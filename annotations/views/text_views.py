"""
Provides views onto :class:`.Text`\s.
"""

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Q

from annotations.display_helpers import get_snippet_relation
from annotations.forms import UploadFileForm
from annotations.models import Text, Appellation, RelationSet
from annotations.utils import basepath
from annotations.tasks import handle_file_upload
from annotations.display_helpers import get_appellation_summaries


from itertools import groupby, combinations


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



@ensure_csrf_cookie
def text(request, textid):
    """
    Provides the main text annotation/info view.

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """

    text = get_object_or_404(Text, pk=textid)
    from annotations.annotators import annotator_factory

    annotator = annotator_factory(request, text)

    context_data = {
        'text': text,
        'textid': textid,
        'title': 'Annotate Text',
        'content': annotator.get_content(),
        'baselocation' : basepath(request)
    }

    # If a text is restricted, then the user needs explicit permission to
    #  access it.
    access_conditions = [
        request.user in text.annotators.all(),
        getattr(request.user, 'is_admin', False),
        text.public,
    ]
    # if not any(access_conditions):
    #     # TODO: return a pretty templated response.
    #     raise PermissionDenied
    mode = request.GET.get('mode', 'view')

    if all([request.user.is_authenticated(), any(access_conditions), mode == 'annotate']):
        template = "annotations/text.html"
        context_data.update({
            'userid': request.user.id,
            'title': text.title,
        })
        context = context_data
        return render(request, template, context)
    elif all([request.user.is_authenticated(), any(access_conditions), mode == 'user_annotations']):
        appellations = Appellation.objects.filter(occursIn_id=textid,
                                                  asPredicate=False,
                                                  createdBy=request.user.id)
        appellations_data, appellation_creators = get_appellation_summaries(appellations)
        relationset_qs = RelationSet.objects.filter(occursIn=textid,
                                                    createdBy=request.user.id)
        relationsets = _get_relations_data(relationset_qs)

        context_data.update({
            'view': 'user',
        })
    elif mode == 'annotate':
        return HttpResponseRedirect(reverse('login'))

    template = "annotations/text_view.html"

    appellations = Appellation.objects.filter(occursIn_id=textid,
                                              asPredicate=False)
    appellations_data, appellation_creators = get_appellation_summaries(appellations)
    relationset_qs = RelationSet.objects.filter(occursIn=textid)
    relationsets = _get_relations_data(relationset_qs)


    context_data.update({
        'userid': request.user.id,
        'appellations_data': appellations_data,
        'annotators': appellation_creators,
        'relations': relationsets,
        'title': text.title,
    })
    context = context_data
    return render(request, template, context)


#TODO: retire this view.
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
            return HttpResponseRedirect(reverse('text', args=[text.id]) + '?mode=annotate')
    else:
        form = UploadFileForm()

        form.fields['project'].queryset = form.fields['project'].queryset.filter(ownedBy_id=request.user.id)
        if project_id:
            form.fields['project'].initial = project_id

    template = "annotations/upload_file.html"
    context = {
        'user': request.user,
        'form': form,
        'subpath': settings.SUBPATH,
    }
    return render(request, template, context)


def texts(request):
    qs = Text.objects.filter(Q(addedBy=request.user))
    return render(request, 'annotations/list_texts.html', {'object_list': qs})


def text_public(request, text_id):
    """
    Detail view for texts to which the user does not have direct access.
    """
    from annotations.filters import RelationSetFilter
    text = get_object_or_404(Text, pk=text_id)

    filtered = RelationSetFilter({'occursIn': text.uri}, queryset=RelationSet.objects.all())
    relations = filtered.qs

    context = {
        'text': text,
        'relations': relations,
    }
    return render(request, 'annotations/text_public.html', context)
