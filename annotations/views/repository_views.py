"""
Provides views related to external repositories.
"""
from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

from annotations import annotators
from annotations.models import Text, TextCollection, RelationSet, Annotation
from annotations.serializers import RepositorySerializer, TextSerializer, RelationSetSerializer
from repository.models import Repository


class RepositoryViewSet(viewsets.ModelViewSet):
    queryset = Repository.objects.all()
    serializer_class = RepositorySerializer

    def retrieve(self, request, pk=None):
        queryset = self.get_queryset()
        repository = get_object_or_404(queryset, pk=pk)
        manager = repository.manager(request.user)
        collections = manager.collections()
        return Response({
            **self.serializer_class(repository).data,
            'collections': collections
        })


class RepositoryCollectionViewSet(viewsets.ViewSet):
    def list(self, request, repository_pk=None):
        repository = get_object_or_404(Repository, pk=repository_pk)
        manager = repository.manager(request.user)
        collections = manager.collections()
        return Response(collections)

    @action(detail=False, methods=['get'])
    def search(self, request, repository_pk=None):
        query = request.query_params.get('q', '')
        if not query:
            return Response([])
        
        repository = get_object_or_404(Repository, pk=repository_pk)
        manager = repository.manager(request.user)
        results = manager.search(query=query)
        return Response(results)

    def retrieve(self, request, pk=None, repository_pk=None):
        repository = get_object_or_404(Repository, pk=repository_pk)
        manager = repository.manager(request.user)
        collection = manager.collection(id=pk)
        return Response(collection)

class RepositoryTextView(viewsets.ViewSet):
    def retrieve(self, request, pk=None, repository_pk=None):
        project_id = request.query_params.get('project_id', None)
        part_of_project = None
        if project_id:
            project = get_object_or_404(TextCollection, pk=int(project_id))
            try:
                project.texts.get(repository_source_id=pk)
                part_of_project = {
                    'id': project.id,
                    'name': project.name
                }
            except Text.DoesNotExist:
                pass
        repository = get_object_or_404(Repository, pk=repository_pk)
        manager = repository.manager(request.user)
        result = manager.resource(id=int(pk))

        try:
            master_text = Text.objects.get(uri=result.get('uri'))
        except Text.DoesNotExist:
            master_text = Text.objects.create(uri=result.get('uri'),title=result.get('name'),public=result.get('public'),content_type=result.get('content_types'),repository_source_id=result.get('id'),repository_id=repository_pk,addedBy_id=1)
        aggregate_content = result.get('aggregate_content')

        submitted = Annotation.objects.filter(occursIn_id=master_text.id, submitted=True)

        context = {
            'result': result,
            'master_text': TextSerializer(master_text).data if master_text else None,
            'part_of_project': part_of_project,
            'submitted': True if submitted else None
        }
        if master_text:
            relations = RelationSet.objects.filter(Q(occursIn=master_text) | Q(occursIn_id__in=master_text.children)).order_by('-created')[:10]
            context['relations'] = RelationSetSerializer(relations, many=True, context={'request': request}).data
        return Response(context)

class RepositoryTextContentViewSet(viewsets.ViewSet):
    def retrieve(self, request, pk=None, repository_pk=None, texts_pk=None):
        repository = get_object_or_404(Repository, pk=repository_pk)
        manager = repository.manager(request.user)

        try:
            content = manager.content(id=pk)
            resource = manager.resource(id=texts_pk)
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
                master = manager.resource(id=int(part_of_id))
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
