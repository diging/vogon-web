from django.http import HttpResponse
from django.template import RequestContext, loader


def custom_403_handler(request):
    """
    Default 403 Handler. This method gets invoked if a PermissionDenied
    Exception is raised.

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
        Status 403.
    """
    template = loader.get_template('annotations/forbidden_error_page.html')
    context_data = {
        'userid': request.user.id,
        'error_message': "Whoops, you're not supposed to be here!"
    }
    context = RequestContext(request, context_data)
    return HttpResponse(template.render(context), status=403)
