from django.conf import settings
from social.apps.django_app.default.models import UserSocialAuth


def jars_github_auth(user):
    """
    Build an auth header for Amphora using ``user``'s Github access token.
    """
    try:
        token = user.social_auth.get(provider='github').extra_data.get('access_token')
    except UserSocialAuth.DoesNotExist:
        return {}

    auth_token = ':'.join([settings.SOCIAL_AUTH_GITHUB_KEY,
                           settings.SOCIAL_AUTH_GITHUB_SECRET,
                           token])
    return {'Authorization': 'GithubToken %s' % auth_token}
