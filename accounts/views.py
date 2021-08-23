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
from accounts.serializers import UserSerializer, TokenObtainPairSerializer, ResetPasswordSerializer
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
		print(settings.CITESPHERE_CLIENT_ID)
		print(settings.CITESPHERE_CLIENT_SECRET)
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
		print("request object", r.json())
		token.access_token = r.json()["access_token"]
		token.refresh_token = r.json()["refresh_token"]
		token.save()
		return Response(status=status.HTTP_201_CREATED)

class ForgotPasswordView(APIView):
    def post(self, request):
        username = request.data.get('username', None)
        if username:
            try:
                user = VogonUser.objects.get(username=username)
            except VogonUser.DoesNotExist:
                return Response({ "success": False, "message": "User not found" }, status=404)
            token = jwt.encode({ 
                'exp': arrow.utcnow().shift(days=1).timestamp,
                'username': user.username,
            }, settings.SECRET_KEY, algorithm='HS256').decode('UTF-8')
            reset_token = ResetToken(user=user, token=token)
            reset_token.save()

            # Email token
            send_mail(
                'Vogon password reset',
                f'Reset link: {settings.EMAIL_RESET_LINK}/{token}',
                settings.EMAIL_SENDER_ID,
                [user.email],
                fail_silently=False,
            )

            return Response({ "success": True })
        return Response({ "success": False, "message": "Username not specified" }, status=400)

class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)

        if serializer.is_valid():
            username = serializer.data.get('username')
            password1 = serializer.data.get('password1')
            password2 = serializer.data.get('password2')
            token = serializer.data.get('token')

            if password1 == password2:
                user = get_object_or_404(VogonUser, username=username)
                
                # Check if this token was generated
                reset_token = get_object_or_404(ResetToken, user=user, token=token)

                # Verify token
                try:
                    decoded = jwt.decode(reset_token.token, settings.SECRET_KEY, algorithms='HS256')

                    # Ensure token is created by the same user
                    if decoded['username'] == user.username:
                        user.set_password(password1)
                        user.save()
                        reset_token.delete()
                        return Response({
                            "success": True,
                            "message": "Successfully reset the password!"
                        })
                    return Response({
                        "success": False,
                        "message": "Invalid reset link! Try resetting again..."
                    }, status=403)
                except jwt.exceptions.PyJWTError:
                    return Response({
                        "success": False,
                        "message": "Invalid reset link! Try resetting again..."
                    }, status=403)

            else:
                return Response({
                    "success": False,
                    "message": "Passwords does not match"
                }, status=400)
        else:
            return Response({
                "success": False,
                "message": "Specify all the fields"
            }, status=400)


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
		return Response({})

	@action(detail=True, methods=['post'], url_name='markasdeleted')
	def mark_as_deleted(self, request, pk=None):
		notification = Notification.objects.filter(pk=pk, recipient=request.user)
		notification.mark_all_as_deleted()
		return Response({})

	@action(detail=False, methods=['post'], url_name='markallasdeleted')
	def mark_all_as_deleted(self, request):
		notifications = Notification.objects.filter(recipient=request.user, deleted=False)
		notifications.mark_all_as_deleted()
		return Response({})
