from django.shortcuts import render
from annotations.models import VogonUser
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate, get_user_model
from accounts.serializers import UserSerializer
from rest_framework import permissions, status, viewsets
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import TokenObtainPairSerializer
from rest_framework.decorators import api_view
import requests
from django.conf import settings
from .models import GithubToken
import logging


class UserViewSet(viewsets.ModelViewSet):
    """
	API endpoint that allows users to be viewed or edited.
	"""

    User = get_user_model()
    queryset = VogonUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)


@api_view(["GET"])
def github_token(request):
    """
    List all code snippets, or create a new snippet.
    """
    logger = logging.getLogger(__name__)
    if request.method == "GET":
        code = request.GET.get("code", "")
        logger.error(code)
        print(code)
        r = requests.post(
            "https://github.com/login/oauth/access_token",
            params={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_SECRET_ID,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        try:
            token = GithubToken.objects.get(user=request.user)
        except GithubToken.DoesNotExist:
            token = GithubToken()
            token.user = request.user
        logger.error(r.json())
        token.token = r.json()["access_token"]
        token.save()
        return Response(status=status.HTTP_201_CREATED)


class TokenObtainPairView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer
