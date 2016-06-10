from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader

from annotations.models import Text, Appellation, RelationSet
from annotations.utils import basepath
from annotations.display_helpers import get_appellation_summaries

from guardian.shortcuts import get_perms


@ensure_csrf_cookie
def text(request, textid):
    """
    Provides the main text view.

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """

    text = get_object_or_404(Text, pk=textid)
    context_data = {
        'text': text,
        'textid': textid,
        'title': 'Annotate Text',
        'baselocation' : basepath(request)
    }

    # If a text is restricted, then the user needs explicit permission to
    #  access it.
    access_conditions = [
        'view_text' in get_perms(request.user, text),
        request.user in text.annotators.all(),
        getattr(request.user, 'is_admin', False),
        text.public,
    ]
    # if not any(access_conditions):
    #     # TODO: return a pretty templated response.
    #     raise PermissionDenied
    mode = request.GET.get('mode', 'view')

    if all([request.user.is_authenticated(), any(access_conditions), mode == 'annotate']):
        template = loader.get_template('annotations/text.html')
        context_data.update({
            'userid': request.user.id,
            'title': text.title,
        })
        context = RequestContext(request, context_data)
        return HttpResponse(template.render(context))
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

    template = loader.get_template('annotations/text_view.html')

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
    context = RequestContext(request, context_data)
    return HttpResponse(template.render(context))
