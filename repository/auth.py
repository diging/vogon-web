from django.conf import settings
from allauth.socialaccount.models import SocialToken, SocialAccount


def jars_github_auth(user):
    """
    Build an auth header for Amphora using ``user``'s Github access token.
    """
    try:
        user_account = SocialAccount.objects.filter(user=user, provider='github')[:1].get()
        token = SocialToken.objects.filter(account=user_account)[:1].get()
    except SocialAccount.DoesNotExist:
        return {}

    auth_token = token #':'.join([settings.SOCIAL_AUTH_GITHUB_KEY,
                        #    settings.SOCIAL_AUTH_GITHUB_SECRET,
                        #    token])
    return {'Authorization': 'GithubToken %s' % auth_token}


def giles_auth(user):
    """
    Build an auth header for Giles.
    """
    import giles
    return {'Authorization': 'token %s' % giles.get_user_auth_token(user)}
