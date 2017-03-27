from django.conf import settings


def google(request):
    return {'google_analytics_id': getattr(settings, 'GOOGLE_ANALYTICS_ID', None)}


def version(request):
    return {'VERSION': getattr(settings, 'VERSION', None)}


def base_url(request):
    base_url = settings.BASE_URL
    if base_url.endswith('/'):
        base_url = base_url[:-1]
    return {'base_url': base_url}
