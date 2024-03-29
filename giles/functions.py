from django.conf import settings

from giles.models import GilesToken

import requests

_fix_url = lambda url: url.replace('http://', 'https://') if url is not None else None



def handle_status_exception(func):
    def wrapper(user, *args, **kwargs):
        response = func(user, *args, **kwargs)
        if response.status_code == 401:    # Auth token expired.
            try:
                user.giles_token.delete()
            except AssertionError:
                pass

            get_user_auth_token(user, **kwargs)
            user.refresh_from_db()
            # TODO: we could put some Exception handling here.
            return func(user, *args, **kwargs)
        elif response.status_code != requests.codes.ok and response.status_code != 202:
            message = 'Status %i, content: %s' % (response.status_code, response.content)
            logger.error(message)
            raise StatusException(response)
        return response
    return wrapper


def api_request(func):
    def wrapper(user, *args, **kwargs):
        response = func(user, *args, **kwargs)
        return response.status_code, response.json()
    return wrapper


def _create_auth_header(user, **kwargs):
    provider = kwargs.get('provider', settings.GILES_DEFAULT_PROVIDER)
    # token = user.social_auth.get(provider=provider).extra_data['access_token']
    token = get_user_auth_token(user)
    return {'Authorization': 'token %s' % token}


def get_user_auth_token(user, **kwargs):
    """
    Get the current auth token for a :class:`.User`\.

    If the user has no auth token, retrieve one and store it.

    Supports dependency injection.

    Parameters
    ----------
    user : :class:`django.contrib.auth.User`
    kwargs : kwargs

    Returns
    -------
    str
        Giles authorization token for ``user``.
    """
    fresh = kwargs.get('fresh', False)
    try:
        if user.giles_token and not fresh:
            return user.giles_token.token
    except AttributeError:    # RelatedObjectDoesNotExist.
        pass    # Will proceed to retrieve token.

    try:
        status_code, data = get_auth_token(user, **kwargs)
        try:
            user.giles_token.delete()
        except Exception as E:
            raise E
        
        user.giles_token = GilesToken.objects.create(for_user=user, token=data["token"])
        user.save()
        return user.giles_token.token
    except Exception as E:
        print((str(E)))
        print((status_code, data))
        template = "Failed to retrieve access token for user {u}"
        msg = template.format(u=user.username)
        if kwargs.get('raise_exception', False):
            raise E
        logger.error(msg)
        logger.error(str(E))


# @handle_status_exception
@api_request
def get_auth_token(user, **kwargs):
    """
    Obtain and store a short-lived authorization token from Giles.

    See https://diging.atlassian.net/wiki/display/GIL/REST+Authentication.
    """
    giles = kwargs.get('giles', settings.GILES)
    post = kwargs.get('post', settings.POST)
    provider = kwargs.get('provider', settings.GILES_DEFAULT_PROVIDER)
    app_token = kwargs.get('app_token', settings.GILES_APP_TOKEN)

    path = '/'.join([giles, 'rest', 'token'])
    provider_token = user.social_auth.get(provider=provider)\
                                     .extra_data.get('access_token')

    return post(path, data={'providerToken': provider_token},
                headers={'Authorization': 'token %s' % app_token})




def format_giles_url(url, user, dw=300):
    """
    """
    return url + '&accessToken=' + get_user_auth_token(user) + '&dw=%i' % 300
