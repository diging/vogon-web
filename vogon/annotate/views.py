from django.shortcuts import render
from django.http import HttpResponse
from django.template import RequestContext, loader

import hashlib

# Create your views here.
def text(request, textid):
    template = loader.get_template('annotate/text.html')
    hashable = '|'.join([request.user.username, request.user.password])
    context = RequestContext(request, {
        'textid': textid,
        'userid': request.user.id,
		'title': 'Annotate Text',
        'userdigest': hashlib.sha224(hashable).hexdigest(),
    })
    return HttpResponse(template.render(context))
