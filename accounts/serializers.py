from rest_framework import serializers
from annotations.models import VogonUser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import GithubToken, CitesphereToken

class UserSerializer(serializers.ModelSerializer):
	def create(self, validated_data):
		for k,v in validated_data.items():
			print(k,v)
		user = VogonUser.objects.create(
			email=validated_data['email'],
			username=validated_data['username'],
			full_name=validated_data['full_name'],
			affiliation=validated_data['affiliation'],
		)
		user.save()

		return user

	class Meta:
		model = get_user_model()
		fields = ('id','email', 'full_name', 'username', 'affiliation')
		ref_name = "user accounts"


class TokenObtainPairSerializer(TokenObtainPairSerializer):
	@classmethod
	def get_token(cls, user):
		token = super().get_token(user)
		try:
			GithubToken.objects.get(user=user)
			token['github_token'] = True
		except GithubToken.DoesNotExist:
			token['github_token'] = False
		try:
			CitesphereToken.objects.get(user=user)
			token['citesphere_token'] = True
		except CitesphereToken.DoesNotExist:
			token['citesphere_token'] = False
		return token

class ResetPasswordSerializer(serializers.Serializer):
	username = serializers.CharField(required=True)
	password1 = serializers.CharField(required=True)
	password2 = serializers.CharField(required=True)
	token = serializers.CharField(required=True)