from django.conf import settings
from accounts.models import GithubToken

def jars_github_auth(user):
    """
    Build an auth header for Amphora using ``user``'s Github access token.
    """
    # try:
    #     #user_account = SocialAccount.objects.filter(user=user, provider='github')[:1].get()
    #     token = '3f059e2c9931a1ee36022dc8f669d1fc02dff6cb"
    # except SocialAccount.DoesNotExist:
    #     return {}

    auth_token = GithubToken.objects.get(user=user)
    #':'.join([settings.SOCIAL_AUTH_GITHUB_KEY,
                        #    settings.SOCIAL_AUTH_GITHUB_SECRET,
                        #    token])
    return {'Authorization': 'GithubToken %s' % auth_token}


def giles_auth(user):
    """
    Build an auth header for Giles.
    """
    import giles
    return {'Authorization': 'token %s' % giles.get_user_auth_token(user)}
