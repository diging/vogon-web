from django.shortcuts import render
from annotations.models import VogonUser
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate, get_user_model
from accounts.serializers import UserSerializer
from rest_framework import permissions, status, viewsets
# Create your views here.
class UserViewSet(viewsets.ModelViewSet):
	"""
	API endpoint that allows users to be viewed or edited.
	"""
	User = get_user_model()
	queryset = VogonUser.objects.all()
	serializer_class = UserSerializer
	permission_classes = (AllowAny,)