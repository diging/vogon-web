from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.shortcuts import get_object_or_404, render
from django.db.models.expressions import DateTime
from django.views.decorators.csrf import ensure_csrf_cookie

from annotations.models import Relation, Appellation, VogonUser, Text
from annotations.annotators import annotator_factory


@login_required
@ensure_csrf_cookie
def annotate(request, text_id):
    text = get_object_or_404(Text, pk=text_id)
    annotator = annotator_factory(request, text)
    return annotator.render()


@login_required
def annotate_image(request, text_id):
    template = loader.get_template('annotations/annotate_image.html')
    text = Text.objects.get(pk=text_id)

    return HttpResponse(template.render(context))
