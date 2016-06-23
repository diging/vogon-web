from django.http import HttpResponse
from django.template import RequestContext, loader
from django.db.models.expressions import DateTime

from annotations.models import Relation, Appellation, VogonUser, Text



def annotate_image(request):
    template = loader.get_template('annotations/annotate_image.html')
    context = RequestContext(request, {})
    return HttpResponse(template.render(context))
