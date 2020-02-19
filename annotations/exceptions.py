from django.http import HttpResponse


def custom_403_handler(request, exception):
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
    template = loader.get_template()
    context = {
        'userid': request.user.id,
        'error_message': "Whoops, you're not supposed to be here!"
    }

    return render(request, 'annotations/forbidden_error_page.html', context, status=403)
