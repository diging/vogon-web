from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from annotations.models import VogonUser

class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Invoked just after a user successfully authenticates via a
        social provider, but before the login is actually processed
        (and before the pre_social_login signal is emitted).

        We're trying to solve different use cases:
        - social account already exists, just go on
        - social account exists, link social account to existing user
        """
        # Ignore existing social accounts, just do this stuff for new ones
        if sociallogin.is_existing:
            return

        # check if given email address already exists.
        # Note: __iexact is used to ignore cases
        try:
            username = sociallogin.account.extra_data['login'].lower()
            user = VogonUser.objects.get(username__iexact=username)

        # if it does not, let allauth take care of this new social account
        except VogonUser.DoesNotExist:
            return

        # if it does, connect this new social login to the existing user
        sociallogin.connect(request, user)