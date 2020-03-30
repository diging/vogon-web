"""
Provides user-oriented views, including dashboard, registration, etc.
"""
import arrow
from itertools import groupby
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core import serializers
from django.db.models import Q, Count
from django.db.models.functions import Trunc
from django.shortcuts import get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from rest_framework.decorators import permission_classes, authentication_classes, action
from rest_framework.permissions import AllowAny
from rest_framework import viewsets
from rest_framework.response import Response

from annotations.models import (VogonUser, Text, Appellation, RelationSet,
								Relation)
from annotations.serializers import (
	ProjectSerializer, TextSerializer, RelationSetSerializer,
	UserSerializer, TextCollectionSerializer
)
from accounts.serializers import UserSerializer as VogonUserSerializer



class VogonUserAuthenticationForm(AuthenticationForm):
	class Meta:
		model = VogonUser


class UserViewSet(viewsets.ModelViewSet):
	"""
	User list, detail page and dashboard
	"""
	queryset = VogonUser.objects.exclude(id=-1).order_by('username')
	serializer_class = VogonUserSerializer

	def list(self, *args, **kwargs):
		queryset = self.get_queryset()
		serializer = UserSerializer

		self.page = self.paginate_queryset(queryset)
		if self.page is not None:
			serializer = UserSerializer(self.page, many=True)
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
		relations = RelationSetSerializer(relations_qs, many=True, context={'request': request}).data

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

	@action(detail=False, methods=['get'])
	def dashboard(self, request):
		"""
		User's dashboard page
		
			* Recently annotated texts
			* Recently added texts
			* Recent projects
			* Recent annotations
		"""
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

	@authentication_classes([])
	@permission_classes([AllowAny])
	def create(self, request):
		return super().create(request)

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
			annotation_count=Count('appellation', distinct=True),
			relation_count=Count('relation', distinct=True),
			text_count=Count('addedTexts', distinct=True)
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


