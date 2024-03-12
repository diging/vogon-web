from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from annotations.models import Text
from annotations.serializers import RepositorySerializer, TextSerializer
from repository.models import Repository
from annotations.views.utils import _get_project, _transfer_text, get_giles_file_data, _get_project_details

class CitesphereRepoViewSet(viewsets.ViewSet):
    queryset = Repository.objects.all()

    def retrieve(self, request, pk):
        queryset = Repository.objects.filter(repo_type=Repository.CITESPHERE)
        repository = get_object_or_404(queryset, pk=pk)

        manager = repository.manager(request.user)
        groups = manager.groups()
        return Response({
            **RepositorySerializer(repository).data,
            'groups': groups
        })


class CitesphereGroupsViewSet(viewsets.ViewSet):
    def list(self, request, repository_pk=None):
        repository = get_object_or_404(
            Repository,
            pk=repository_pk,
            repo_type=Repository.CITESPHERE
        )
        manager = repository.manager(request.user)
        groups = manager.groups()
        return Response(groups)

    def retrieve(self, request, repository_pk, pk):
        repository = get_object_or_404(
            Repository,
            pk=repository_pk,
            repo_type=Repository.CITESPHERE
        )
        error = []
        manager = repository.manager(request.user)
        if manager:
            collections = manager.group_collections(pk)
            items = manager.group_items(pk)
        else:
            error = ["Manager", 404]
        if isinstance(items, tuple):
            error = ["Items", items[1]]
        if isinstance(collections, tuple):
            error = ["Collections", collections[1]]
        if error:
            return Response({ "message": f"Citesphere {error[1]} error: {error[0]}" }, error[1])
        
        # Append `children` field
        for collection in collections["collections"]:
            if collection["numberOfCollections"] > 0:
                collection["children"] = []

        result = {
            **collections,
            "items": items["items"]
        }

        return Response(result)


class CitesphereCollectionsViewSet(viewsets.ViewSet):
    def list(self, request, repository_pk, groups_pk):
        repository = get_object_or_404(
            Repository,
            pk=repository_pk,
            repo_type=Repository.CITESPHERE
        )
        manager = repository.manager(request.user)
        collections = manager.group_collections(groups_pk)
        return Response(collections)

    @action(detail=True, methods=['get'])
    def collections(self, request, repository_pk, groups_pk, pk):
        repository = get_object_or_404(
            Repository,
            pk=repository_pk,
            repo_type=Repository.CITESPHERE
        )
        manager = repository.manager(request.user)
        collections = manager.collection_collections(groups_pk, pk)
        for collection in collections["collections"]:
            if collection["numberOfCollections"] > 0:
                collection["children"] = []

        return Response(collections)

    @action(detail=True, methods=['get'])
    def items(self, request, repository_pk, groups_pk, pk):
        repository = get_object_or_404(
            Repository,
            pk=repository_pk,
            repo_type=Repository.CITESPHERE
        )
        manager = repository.manager(request.user)
        page = request.query_params.get('page', 1)
        items = manager.collection_items(groups_pk, pk, page)
        return Response(items)


class CitesphereItemsViewSet(viewsets.ViewSet):
    def list(self, request, repository_pk, groups_pk):
        repository = get_object_or_404(
            Repository,
            pk=repository_pk,
            repo_type=Repository.CITESPHERE
        )
        manager = repository.manager(request.user)
        page = request.query_params.get('page', 1)
        items = manager.group_items(groups_pk, page)
        return Response(items)
    
    def retrieve(self, request, repository_pk, groups_pk, pk):
        part_of_id = self.request.query_params.get('part_of', None)
        found, project_details = _get_project_details(request)
        if not found:
            return Response({ "message": "Project not found" }, 404)
        repository = get_object_or_404(
            Repository,
            pk=repository_pk,
            repo_type=Repository.CITESPHERE
        )
        manager = repository.manager(request.user)
        item_data = manager.group_item(groups_pk, pk)
        try:
            if item_data[0] == "error":
                return Response(status=item_data[1])
        except Exception:
            pass
        data = item_data['item']['gilesUploads']
        result = data[0]
        master_text = None
        result_data = result['uploadedFile']
        try:
            master_text = Text.objects.get(uri=result_data.get('url'))
        except Text.DoesNotExist:
            try:
                master_text = Text.objects.create(
                    uri=result_data.get('url'),
                    title=result_data.get('filename'),
                    file_id=pk,
                    group_id=groups_pk,
                    content_type=[result_data.get('content-type')],
                    repository_id=repository_pk,
                    addedBy=request.user,
                )
            except Exception:
                pass
        if part_of_id:
            master_text.repository_source_id = part_of_id
        master_text.repository_source_id = repository_pk
        submitted = False
        context = {
            'item_data': item_data,
            'master_text': TextSerializer(master_text).data if master_text else None,
            'part_of_project': project_details,
            'submitted': submitted,
            'project_details': project_details,
            'result': result,
            'repository': RepositorySerializer(repository).data,
        }
        return Response(context)
    
    @action(detail=True, methods=['get'], url_name='retrieve_text')
    def retrieve_text(self, request, repository_pk, groups_pk, pk):
        repository = get_object_or_404(Repository, pk=repository_pk, repo_type=Repository.CITESPHERE)
        manager = repository.manager(request.user)
        item_data = manager.group_item(groups_pk, pk)
        file_url = request.query_params.get('file_url', None)
        try:
            if item_data[0] == "error":
                return Response(status=item_data[1])
        except Exception as e:
            pass
        data = item_data['item']['gilesUploads']
        result = data[0]
        master_text = None
        result_data = get_giles_file_data(result, file_url)
        try:
            master_text = Text.objects.get(uri=result_data.get('url'))
        except Text.DoesNotExist:
            try:
                master_text = Text.objects.create(
                    uri=result_data.get('url'),
                    title=result_data.get('filename'),
                    file_id=pk,
                    group_id=groups_pk,
                    content_type=result_data.get('content-type'),
                    repository_id=repository_pk,
                    addedBy=request.user
                )
            except APIException as e:
                return Response({
                    "message": e.detail["message"]
                }, e.detail["code"])
        project_id = self.request.query_params.get('project_id', None)
        return Response({
            'success': True,
            'text_id': master_text.id,
            'project_id': project_id,
        })
    
    @action(detail=True, methods=['get'], url_name='file')
    def get_file(self, request, repository_pk, groups_pk, pk):
        file_id = request.query_params.get('file_id', None)
        if not file_id:
            return Response(data="file not provided", status=status.HTTP_400_BAD_REQUEST)
        repository = get_object_or_404(
            Repository,
            pk=repository_pk,
            repo_type=Repository.CITESPHERE
        )
        manager = repository.manager(request.user)
        file_content = manager.content(groups_pk, pk, file_id)
        try:
            if file_content[0] == "error":
                return Response(status=file_content[1])
        except Exception:
            return Response(data=file_content, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_name='transfertext')
    def transfer_to_project(self, request, repository_pk, groups_pk, pk):
        text = get_object_or_404(Text, pk=request.data.get('text_id', None))
        
        try:
            # Retrieve current and target project
            current_project = _get_project(request, 'project_id')
            target_project = _get_project(request, 'target_project_id')

            # Transfer text
            _transfer_text(text, current_project, target_project, request.user)
            
            return Response({
                "message": "Successfully transferred text, appellations, and relations"
            })
        except APIException as e:
            return Response({
                "message": e.detail["message"]
            }, e.detail["code"])
    