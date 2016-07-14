from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.template import RequestContext, loader
from django.db.models.expressions import DateTime

from annotations.models import Relation, Appellation, VogonUser, Text


@login_required
def annotate_image(request, text_id):
    template = loader.get_template('annotations/annotate_image.html')
    text = Text.objects.get(pk=text_id)
    context = RequestContext(request, {
        'textid': text.id,
        'userid': request.user.id,
        'text': text,
    })
    return HttpResponse(template.render(context))
