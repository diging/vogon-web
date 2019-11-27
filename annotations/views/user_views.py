"""
Provides user-oriented views, including dashboard, registration, etc.
"""
import json
import arrow
from itertools import groupby
from django.conf import settings
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core import serializers
from django.db.models import Q, Count
from django.db.models.functions import Trunc
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.forms import AuthenticationForm
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.response import Response

# TODO: should we be using VogonGroup?
from django.contrib.auth.models import Group

from annotations.models import (VogonUser, Text, Appellation, RelationSet,
								TextCollection, Relation)
from annotations.forms import RegistrationForm, UserChangeForm
from annotations.display_helpers import user_recent_texts
from annotations.serializers import (
	ProjectSerializer, TextSerializer, RelationSetSerializer,
	UserSerializer, TextCollectionSerializer, RelationSetSerializer
)

import datetime
from isoweek import Week


class VogonUserAuthenticationForm(AuthenticationForm):
	class Meta:
		model = VogonUser


class DashboardView(APIView):
	"""
	User's dashboard page
	
		* Recently annotated texts
		* Recently added texts
		* Recent projects
		* Recent annotations
	"""
	def get(self, request):
		fields = ['id', 'name', 'description']
		projects = ProjectSerializer(
			request.user.collections.all()[:5], many=True
		).data
		projects_contributed = ProjectSerializer(
			request.user.contributes_to.all()[:5], many=True
		).data

		# Retrieve a unique list of texts that were recently annotated by the user.
		#  Since many annotations will be on "subtexts" (i.e. Texts that are
		#  part_of another Text), we need to first identify the unique subtexts,
		#  and then assemble a list of unique "top level" texts.
		_recently_annotated = request.user.appellation_set \
				.order_by('occursIn_id', '-created') \
				.values_list('occursIn_id')[:20]
			
		_annotated_texts = Text.objects.filter(pk__in=_recently_annotated)
		_key = lambda t: t.id
		_recent_grouper = groupby(
			sorted(
				[t.top_level_text for t in _annotated_texts],
				key=_key
			),
			key=_key
		)
		_recent_texts = []
		for t_id, group in _recent_grouper:
			_recent_texts.append(next(group))
		_recent_texts = _recent_texts[:5]
		recent_texts = TextSerializer(_recent_texts, many=True).data

		_added_texts = Text.objects.filter(
				addedBy_id=request.user.id, 
				part_of__isnull=True
			) \
			.order_by('-added')[:5]
		added_texts = TextSerializer(_added_texts, many=True).data

		appellation_qs = Appellation.objects.filter(createdBy__pk=request.user.id) \
										.filter(asPredicate=False) \
										.distinct().count()
		relationset_qs = RelationSet.objects.filter(createdBy__pk=request.user.id) \
										.distinct().count()

		_relations = RelationSet.objects.filter(createdBy=request.user) \
				.order_by('-created')[:10]

		relations = RelationSetSerializer(_relations, many=True, context={'request': request}).data
		return Response({ 
			'user': UserSerializer(request.user).data,
			'projects': projects,
			'projects_contributed': projects_contributed,
			'recent_texts': recent_texts,
			'added_texts': added_texts,
			'appellation_count': appellation_qs,
			'relation_count': relationset_qs,
			'relations': relations
		})

class UserViewSet(viewsets.ModelViewSet):
	"""
	User list and detail page
	"""
	queryset = VogonUser.objects.exclude(id=-1).order_by('username')
	serializer_class = UserSerializer

	def list(self, *args, **kwargs):
		queryset = self.get_queryset()
		serializer = self.get_serializer_class()

		self.page = self.paginate_queryset(queryset)
		if self.page is not None:
			serializer = self.get_serializer(self.page, many=True)
			return self.get_paginated_response(serializer.data)
		else:
			users = serializer(queryset, many=True).data
			
		return Response(users)

	def retrieve(self, request, pk=None):
		user = get_object_or_404(VogonUser, pk=pk)
		user_data = UserSerializer(user).data
		appellation_count = user.appellation_set.count()
		relation_count = user.relation_set.count()
		text_count = Text.objects.filter(appellation__createdBy=user) \
			.distinct().count()

		project_qs = user.collections.all().annotate(
			num_texts=Count('texts'),
			num_relations=Count('texts__relationsets')
		)
		projects = TextCollectionSerializer(project_qs, many=True).data

		relations_qs = RelationSet.objects.filter(createdBy=user) \
			.order_by('-created')[:10]
		relations = RelationSetSerializer(relations_qs, many=True).data

		weekly_annotations = self.get_weekly_annotations(user)

		return Response({
			**user_data,
			'appellation_count': appellation_count,
			'relation_count': relation_count,
			'text_count': text_count,
			'projects': projects,
			'relations': relations,
			'weekly_annotations': weekly_annotations
		})

	def get_paginated_response(self, data):
		return Response({
			'count':len(self.get_queryset()),
			'results': data,
		})

	def get_queryset(self, *args, **kwargs):
		queryset = super(UserViewSet, self).get_queryset(*args, **kwargs)
		search = self.request.query_params.get('search', None)
		if search:
			queryset = queryset.filter(
				Q(full_name__icontains=search) |
				Q(username__icontains=search)
			)
		queryset = queryset.annotate(
			annotation_count=Count('appellation'),
			relation_count=Count('relation'),
			text_count=Count('addedTexts')
		)
		return queryset

	def get_weekly_annotations(self, user):
		today = arrow.get()
		week_start = today.shift(days=1-today.isoweekday())
		end = arrow.get(
			week_start.year,
			week_start.month,
			week_start.day
		)
		start = end.shift(weeks=-8)

		relations_by_user = Relation.objects.filter(
				createdBy = user,
				created__gt = start.datetime
			).extra({'date' : 'date(created)'}).values('date') \
			.annotate(count = Count('created')) \
			.annotate(week_date = Trunc('created', 'week'))
		appelations_by_user = Appellation.objects.filter(
				createdBy = user,
				created__gt = start.datetime
			).extra({'date' : 'date(created)'}).values('date') \
			.annotate(count = Count('created')) \
			.annotate(week_date = Trunc('created', 'week'))
		annotation_by_user = list(relations_by_user)
		annotation_by_user.extend(list(appelations_by_user))

		grouped = groupby(annotation_by_user, lambda x:  x['week_date'])

		weekly_annotations = {}
		for week, group in grouped:
			annotations = list(group)
			count = sum([x['count'] for x in annotations])
			weekly_annotations[week] = count
		
		result = []
		for week in arrow.Arrow.range('week', start, end):
			result.append({
				'week': week.datetime,
				'count': weekly_annotations.get(week.datetime, 0)
			})
		return result


@login_required
def logout_view(request):
	logout(request)
	next_page = request.GET.get('next', reverse('home'))
	return HttpResponseRedirect(next_page)
	# return HttpResponseRedirect('/')


@csrf_protect
def login_view(request):
	# We're just using the AuthenticationForm to build the HTML input elements.
	form = AuthenticationForm()
	if request.method == 'POST':
		username = request.POST.get('username')
		password = request.POST.get('password')
		user = authenticate(username=username, password=password)
		if user:
			login(request, user)
			next_page = request.GET.get('next', reverse('dashboard'))
			return HttpResponseRedirect(next_page)
	context = {'form': form}
	return render(request, 'registration/login.html', context)





@csrf_protect
def register(request):
	"""
	Provide new user registration view.

	Parameters
	----------
	request : `django.http.requests.HttpRequest`

	Returns
	----------
	:class:`django.http.response.HttpResponse`
	"""
	if request.method == 'POST':
		form = RegistrationForm(request.POST)
		if form.is_valid():
			# TODO: check uniqueness?
			user = VogonUser.objects.create_user(
				form.cleaned_data['username'],
				form.cleaned_data['email'],
				password=form.cleaned_data['password1'],
				full_name=form.cleaned_data['full_name'],
				affiliation=form.cleaned_data['affiliation'],
				location=form.cleaned_data['location'],
				link=form.cleaned_data['link'],
			)

			# TODO: Do we need this anymore?
			public, _ = Group.objects.get_or_create(name='Public')
			user.groups.add(public)
			user.save()    # TODO: redundant?

			new_user = authenticate(username=form.cleaned_data['username'],
									password=form.cleaned_data['password1'])
			# Logs in the new VogonUser.
			login(request, new_user)
			return HttpResponseRedirect(reverse('dashboard'))
	else:
		form = RegistrationForm()

	return render(request, 'registration/register.html', {'form': form})


@login_required
def user_settings(request):
	"""
	User profile settings.

	Parameters
	----------
	request : `django.http.requests.HttpRequest`

	Returns
	----------
	:class:`django.http.response.HttpResponse`
	"""

	if request.method == 'POST':
		form = UserChangeForm(request.POST, instance=request.user)
		if form.is_valid():
			form.save()
			redirect_target = reverse('user_details', args=[request.user.id])
			return HttpResponseRedirect(redirect_target)
	else:
		form = UserChangeForm(instance=request.user)
		# Assign default image in the preview if no profile image is selected
		#  for the user.
		if request.user.imagefile == "" or request.user.imagefile is None:
			request.user.imagefile=settings.DEFAULT_USER_IMAGE

	template = "annotations/settings.html"
	context = {
		'user': request.user,
		'full_name' : request.user.full_name,
		'email' : request.user.email,
		'affiliation' : request.user.affiliation,
		'location' : request.user.location,
		'link' : request.user.link,
		'preview' : request.user.imagefile,
		'form': form,
		'subpath': settings.SUBPATH,
	}
	return render(request, template, context)


@login_required
def user_annotated_texts(request):
	recent_texts = user_recent_texts(request.user)

	context = {
		'title': 'My Texts',
		'user': request.user,
		'recent_texts': recent_texts,
		'added_texts': added_texts,
	}
	return render(request, template, context)


@login_required
def user_projects(request):
	"""
	Shows a list of the current (logged-in) uers's projects.
	"""
	fields = [
		'id',
		'name',
		'created',
		'ownedBy__id',
		'ownedBy__username',
		'description',
		'num_texts',
		'num_relations',
	]
	qs = TextCollection.objects.filter(ownedBy=request.user.id)
	qs = qs.annotate(num_texts=Count('texts'),
					 num_relations=Count('texts__relationsets'))
	qs = qs.values(*fields)

	template = "annotations/project_user.html"
	context = {
		'user': request.user,
		'title': 'Projects',
		'projects': qs,
	}
	return render(request, template, context)


@login_required
def dashboard(request):
	"""
	Provides the user's personalized dashboard.

	Parameters
	----------
	request : `django.http.requests.HttpRequest`

	Returns
	----------
	:class:`django.http.response.HttpResponse`
	"""
	from itertools import groupby

	template = "annotations/dashboard.html"

	# Retrieve a unique list of texts that were recently annotated by the user.
	#  Since many annotations will be on "subtexts" (i.e. Texts that are
	#  part_of another Text), we need to first identify the unique subtexts,
	#  and then assemble a list of unique "top level" texts.
	_recently_annotated = request.user.appellation_set.order_by('occursIn_id', '-created')\
										   .values_list('occursIn_id')\
										   .distinct('occursIn_id')[:20]
	_annotated_texts = Text.objects.filter(pk__in=_recently_annotated)
	_key = lambda t: t.id
	_recent_grouper = groupby(sorted([t.top_level_text for t in _annotated_texts],
									 key=_key),
							  key=_key)
	recent_texts = []
	for t_id, group in _recent_grouper:
		recent_texts.append(next(group))    # Take the first item only.

	added_texts = Text.objects.filter(addedBy_id=request.user.id, part_of__isnull=True)\
								.order_by('-added')
								# .values('id', 'title', 'added')

	flds = ['id', 'name', 'description']
	projects_owned = request.user.collections.all().values(*flds)
	projects_contributed = request.user.contributes_to.all().values(*flds)

	appellation_qs = Appellation.objects.filter(createdBy__pk=request.user.id)\
										.filter(asPredicate=False)\
										.distinct().count()
	relationset_qs = RelationSet.objects.filter(createdBy__pk=request.user.id)\
										.distinct().count()

	def get_tokens_for_user(user):
		refresh = RefreshToken.for_user(user)
		return {
			'refresh': str(refresh),
			'access': str(refresh.access_token),
		}

	token = get_tokens_for_user(request.user)

	context = {
		'title': 'Dashboard',
		'user': request.user,
		'recent_texts': recent_texts[:5],
		'added_texts': added_texts[:5],
		'projects_owned': projects_owned[:5],
		'projects_contributed': projects_contributed[:5],
		'appellationCount': appellation_qs,
		'relation_count': relationset_qs,
		'relations': RelationSet.objects.filter(createdBy=request.user).order_by('-created')[:10],
		'token': token['access']
	}
	return render(request, template, context)


def user_details(request, userid, *args, **kwargs):
	"""
	Provides users with their own profile view and public profile view of other users in case they are loggedIn.
	Provides users with public profile page in case they are not loggedIn
	----------
	request : HTTPRequest
		The request for fetching user details
	userid : int
		The userid of user who's data  needs to be fetched
	args : list
		List of arguments to view
	kwargs : dict
		dict of arugments to view
	Returns
	----------
	:HTTPResponse:
		Renders an user details view based on user's authentication status.
	"""
	user = get_object_or_404(VogonUser, pk=userid)
	if request.user.is_authenticated() and request.user.id == int(userid) and request.GET.get('mode', '') == 'edit':
		return HttpResponseRedirect(reverse('settings'))
	else:
		textCount = Text.objects.filter(addedBy=user).count()
		textAnnotated = Text.objects.filter(appellation__createdBy=user).distinct().count()
		relation_count = user.relation_set.count()
		appellation_count = user.appellation_set.count()
		start_date = datetime.datetime.now() + datetime.timedelta(-60)

		# Count annotations for user by date.
		relations_by_user = Relation.objects.filter(createdBy = user, created__gt = start_date)\
			.extra({'date' : 'date(created)'}).values('date').annotate(count = Count('created'))

		appelations_by_user = Appellation.objects.filter(createdBy = user, created__gt = start_date)\
			.extra({'date' : 'date(created)'}).values('date').annotate(count = Count('created'))

		annotation_by_user = list(relations_by_user)
		annotation_by_user.extend(list(appelations_by_user))

		result = dict()
		weeks_last_date_map = dict()
		d7 = datetime.timedelta( days = 7)
		current_week = datetime.datetime.now() + d7

		# Find out the weeks and their last date in the past 90 days.
		while start_date <= current_week:
			result[(Week(start_date.isocalendar()[0], start_date.isocalendar()[1]).saturday()).strftime('%m-%d-%y')] = 0
			start_date += d7
		time_format = '%Y-%m-%d'

		# Count annotations for each week.
		for count_per_day in annotation_by_user:
			if(isinstance(count_per_day['date'], str)):
				date = datetime.datetime.strptime(count_per_day['date'], time_format)
			else:
				date = count_per_day['date']
			result[(Week(date.isocalendar()[0], date.isocalendar()[1]).saturday()).strftime('%m-%d-%y')] += count_per_day['count']
		annotation_per_week = list()

		# Sort the date and format the data in the format required by d3.js.
		keys = (list(result.keys()))
		keys.sort()
		for key in keys:
			new_format = dict()
			new_format["date"] = key
			new_format["count"] = result[key]
			annotation_per_week.append(new_format)
		annotation_per_week = str(annotation_per_week).replace("'", "\"")

		projects = user.collections.all()

		template = "annotations/user_details_public.html"
		context = {
			'detail_user': user,
			'textCount': textCount,
			'relation_count': relation_count,
			'appellation_count': appellation_count,
			'text_count': textAnnotated,
			'default_user_image' : settings.DEFAULT_USER_IMAGE,
			'annotation_per_week' : annotation_per_week,
			'recent_activity':[],# get_recent_annotations(user=user),
			'projects': projects,
			'relations': RelationSet.objects.filter(createdBy=user).order_by('-created')[:10]
		}
	return render(request, template, context)


def list_user(request):
	"""
	List all the users of Vogon web.

	Parameters
	----------
	request : `django.http.requests.HttpRequest`

	Returns
	----------
	:class:`django.http.response.HttpResponse`
	"""

	template = "annotations/contributors.html"

	search_term = request.GET.get('search_term')
	sort = request.GET.get('sort', 'username')
	queryset = VogonUser.objects.exclude(id=-1).order_by(sort)

	if search_term:
		queryset = queryset.filter(Q(full_name__icontains=search_term) |
								   Q(username__icontains=search_term))

	paginator = Paginator(queryset, 10)

	page = request.GET.get('page')
	try:
		users = paginator.page(page)
	except PageNotAnInteger:
		# If page is not an integer, deliver first page.
		users = paginator.page(1)
	except EmptyPage:
		# If page is out of range (e.g. 9999), deliver last page of results.
		users = paginator.page(paginator.num_pages)

	context = {
		'search_term' : search_term,
		'sort_column' : sort,
		'user_list': users,
		'user': request.user,
		'title': 'Contributors'
	}
	return render(request, template, context)
