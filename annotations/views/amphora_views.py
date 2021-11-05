"""
Provides views related to Amphora repositories.
"""
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.db import transaction
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from django.db import transaction
from rest_framework.decorators import action
from rest_framework.views import APIView

from annotations import annotators
from annotations.models import Text, TextCollection, RelationSet, Appellation
from annotations.serializers import (
    RepositorySerializer, TextSerializer, 
    RelationSetSerializer, ProjectSerializer
)
from annotations.views.utils import get_project_details
from repository.models import Repository
from annotations.views.utils import _get_project, _transfer_text, _get_project_details


class AmphoraRepoViewSet(viewsets.ViewSet):
    queryset = Repository.objects.all()
    serializer_class = RepositorySerializer

    def retrieve(self, request, pk):
        project = get_project_details(request)
        if not project:
            return Response({
                "message": "Project not found!"
            }, 404)

        limit = request.query_params.get('limit', None)
        offset = request.query_params.get('offset', None)
        q = request.query_params.get('q', None)
        user = request.query_params.get('user', None)
        queryset = Repository.objects.filter(repo_type=Repository.AMPHORA)
        repository = get_object_or_404(queryset, pk=pk)
        manager = repository.manager(request.user)
        collections = manager.collections(
            limit=limit,
            offset=offset,
            q=q,
            user=user
        )

        return Response({
            **RepositorySerializer(repository).data,
            'collections': collections,
            'project': ProjectSerializer(project).data,
        })

class AmphoraCollectionViewSet(viewsets.ViewSet):
    def list(self, request, repository_pk=None):
        repository = get_object_or_404(
            Repository,
            pk=repository_pk,
            repo_type=Repository.AMPHORA
        )
        manager = repository.manager(request.user)
        collections = manager.collections()
        return Response(collections)

    @action(detail=False, methods=['get'])
    def search(self, request, repository_pk=None):
        query = request.query_params.get('q', '')
        if not query:
            return Response([])
        
        repository = get_object_or_404(Repository, pk=repository_pk, repo_type=Repository.AMPHORA)
        manager = repository.manager(request.user)
        results = manager.search(query=query)
        return Response(results)

    def retrieve(self, request, pk=None, repository_pk=None):
        project = get_project_details(request)
        if not project:
            return Response({
                "message": "Project not found!"
            }, 404)

        repository = get_object_or_404(Repository, pk=repository_pk, repo_type=Repository.AMPHORA)
        manager = repository.manager(request.user)
        collection = manager.collection(collection_id=pk)
        collection['project'] = ProjectSerializer(project).data
        collection['repository'] = RepositorySerializer(repository).data
        return Response(collection)

class AmphoraTextViewSet(viewsets.ViewSet):
    def retrieve(self, request, pk=None, repository_pk=None):
        found, project_details, part_of_project = self._get_project_details(
            request,
            pk
        )
        if not found:
            return Response({ "message": f"Project not found" }, 404)
        repository = get_object_or_404(Repository, pk=repository_pk, repo_type=Repository.AMPHORA)
        manager = repository.manager(request.user)
        result = manager.resource(resource_id=int(pk))
        
        try:
            master_text = Text.objects.get(uri=result.get('uri'))
        except Text.DoesNotExist:
            master_text = Text.objects.create(
                uri=result.get('uri'),
                title=result.get('name'),
                public=result.get('public'),
                content_type=result.get('content_types'),
                repository_source_id=result.get('id'),
                repository_id=repository_pk,
                addedBy=request.user
            )
        aggregate_content = result.get('aggregate_content')

        submitted = False
        for child in range(len(master_text.children)):
            if Appellation.objects.filter(occursIn_id=master_text.children[child], submitted=True):
                submitted = True
                break

        context = {
            'result': result,
            'master_text': TextSerializer(master_text).data if master_text else None,
            'part_of_project': part_of_project,
            'submitted': submitted,
            'project_details': project_details,
            'repository': RepositorySerializer(repository).data,
        }
        if master_text:
            relations = RelationSet.objects.filter(Q(occursIn=master_text) | Q(occursIn_id__in=master_text.children)).order_by('-created')[:10]
            context['relations'] = RelationSetSerializer(relations, many=True, context={'request': request}).data
        return Response(context)

    @action(detail=True, methods=['post'], url_name='transfertext')
    def transfer_to_project(self, request, pk=None, repository_pk=None):
        repository = get_object_or_404(Repository, pk=repository_pk, repo_type=Repository.AMPHORA)
        manager = repository.manager(request.user)
        result = manager.resource(resource_id=int(pk))
        text = get_object_or_404(Text, uri=result.get('uri'))
        
        try:
            # Retrieve current and target project
            current_project = _get_project(request, 'project_id')
            target_project = _get_project(request, 'target_project_id')

            # Transfer text
            _transfer_text(
                text, current_project, target_project, request.user)
            
            return Response({
                "message": "Successfully transferred text, appellations, and relations"
            })
        except APIException as e:
            return Response({
                "message": e.detail["message"]
            }, e.detail["code"])
    
    def _get_project_details(self, request, pk):
        project = get_project_details(request)
        if not project:
            return False, None, None

        project_details = ProjectSerializer(project).data
        part_of_project = None
        try:
            project.texts.get(repository_source_id=pk)
            part_of_project = project_details
        except Text.DoesNotExist:
            pass
        return True, project_details, part_of_project
    
class AmphoraTextContentViewSet(viewsets.ViewSet):
    def retrieve(self, request, pk=None, repository_pk=None, texts_pk=None):
        repository = get_object_or_404(Repository, pk=repository_pk, repo_type=Repository.AMPHORA)
        manager = repository.manager(request.user)

        try:
            content = manager.content(content_id=pk)
            if not content:
                return Response({
                    'success': False,
                    'error': 'The text is still getting processed. Check back later...'
                }, 400)
            resource = manager.resource(resource_id=texts_pk)
        except IOError:
            return Response({
                'success': False,
                'error': 'There was a problem communicating with the remote repository that contains'
                    'this content. Please go back, and try again'
            }, 500)

        content_type = content.get('content_type', None)
        if not annotators.annotator_exists(content_type):
            return Response({
                'success': False,
                'error': 'Vogon Doesn\'t support this type of annotation',
                'resource': resource,
                'repository': RepositorySerializer(repository).data,
                'content_type': content_type
            })

        resource_text_defaults = {
            'title': resource.get('title'),
            'created': resource.get('created'),
            'repository': repository,
            'repository_source_id': texts_pk,
            'addedBy': request.user,
        }
        part_of_id = self.request.query_params.get('part_of', None)
        if part_of_id:
            try:
                master = manager.resource(resource_id=int(part_of_id))
            except IOError:
                return Response({
                    'success': False,
                    'error': 'There was a problem communicating with the remote repository that contains'
                        'this content. Please go back, and try again'
                }, 500)

            master_resource, _ = Text.objects.get_or_create(
                uri=master['uri'],
                defaults={
                    'title': master.get('title'),
                    'created': master.get('created'),
                    'repository': repository,
                    'repository_source_id': part_of_id,
                    'addedBy': request.user,
                }
            )
            resource_text_defaults.update({'part_of': master_resource})

        resource_text, _ = Text.objects.get_or_create(
            uri=resource['uri'],
            defaults=resource_text_defaults
        )

        project_id = self.request.query_params.get('project_id', None)

        defaults = {
            'title': resource.get('title'),
            'created': resource.get('created'),
            'repository': repository,
            'repository_source_id': pk,
            'addedBy': request.user,
            'content_type': content_type,
            'part_of': resource_text,
            'originalResource': getattr(resource.get('url'), 'value', None),
        }
        text, _ = Text.objects.get_or_create(
            uri=content['uri'],
            defaults=defaults
        )
        return Response({
            'success': True,
            'text_id': text.id,
            'project_id': project_id
        })
