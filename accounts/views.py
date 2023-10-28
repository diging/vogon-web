import arrow
import jwt
import requests
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, render
from django.contrib.auth import authenticate, get_user_model
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt import authentication
from rest_framework_simplejwt.views import TokenObtainPairView, TokenVerifyView

from annotations.models import VogonUser
from accounts.models import ResetToken, GithubToken, CitesphereToken
from accounts.serializers import UserSerializer, TokenObtainPairSerializer
from annotations.serializers import NotificationSerializer
from notifications.models import Notification


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
	if request.method == "GET":
		code = request.GET.get("code", "")
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
		token.token = r.json()["access_token"]
		token.save()
		return Response(status=status.HTTP_201_CREATED)

@api_view(["GET"])
def citesphere_token(request):
	if request.method == "GET":
		code = request.GET.get("code", "")
		r = requests.post(
			f"{settings.CITESPHERE_ENDPOINT}/api/oauth/token",
			params={
				"client_id": settings.CITESPHERE_CLIENT_ID,
				"client_secret": settings.CITESPHERE_CLIENT_SECRET,
				"code": code,
				"grant_type": "authorization_code",
			},
			headers={"Accept": "application/json"},
		)
		try:
			token = CitesphereToken.objects.get(user=request.user)
		except CitesphereToken.DoesNotExist:
			token = CitesphereToken()
			token.user = request.user
		token.access_token = r.json()["access_token"]
		token.refresh_token = r.json()["refresh_token"]
		token.save()
		return Response(status=status.HTTP_201_CREATED)

@api_view(['POST'])
def check_reset_token(request):
	username = request.data.get('username', None)
	token = request.data.get('token', None)
	if username:
		try:
			user = VogonUser.objects.get(username=username)
		except VogonUser.DoesNotExist:
			return Response({ "success": False, "message": "User not found" }, status=status.HTTP_404_NOT_FOUND)
	if user.is_token_reset_required:
		reset_token = ResetToken(user=user, token=token)
		reset_token.save()
		return Response(status=status.HTTP_200_OK)
	else:
		try:
			token = ResetToken.objects.get(user=user, token=token)
		except ResetToken.DoesNotExist:
			return Response({ "success": False, "message": "Reset token not found" }, status=status.HTTP_404_NOT_FOUND)

class TokenObtainPairView(TokenObtainPairView):
	serializer_class = TokenObtainPairSerializer

class VogonTokenVerifyView(TokenVerifyView):
	def post(self, request, *args, **kwargs):
		super().post(request, *args, **kwargs)
		user = authentication.JWTAuthentication().authenticate(request)[0]
		notifications = user.notifications.active()
		return Response({ 
			'notifications': NotificationSerializer(notifications, many=True).data
		}, status=status.HTTP_200_OK)

class NotificationViewset(viewsets.ViewSet):
	@action(detail=True, methods=['post'], url_name='markasread')
	def mark_as_read(self, request, pk=None):
		notification = Notification.objects.filter(pk=pk, recipient=request.user)
		notification.mark_all_as_read()
		return Response({}, status=status.HTTP_200_OK)

	@action(detail=True, methods=['post'], url_name='markasdeleted')
	def mark_as_deleted(self, request, pk=None):
		notification = Notification.objects.filter(pk=pk, recipient=request.user)
		notification.mark_all_as_deleted()
		return Response({}, status=status.HTTP_200_OK)

	@action(detail=False, methods=['post'], url_name='markallasdeleted')
	def mark_all_as_deleted(self, request):
		notifications = Notification.objects.filter(recipient=request.user, deleted=False)
		notifications.mark_all_as_deleted()
		return Response({}, status=status.HTTP_200_OK)
