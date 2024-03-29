import itertools as it
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action

from annotations.models import Relation, Appellation, VogonUser, Text, RelationSet, TextCollection, Repository, DateAppellation
from annotations.annotators import annotator_factory
from annotations.serializers import (RelationSetSerializer,
    ProjectSerializer, UserSerializer, Text2Serializer)
from annotations.filters import RelationSetFilter
from annotations.tasks import submit_relationsets_to_quadriga
from annotations.network import network_data
from concepts.models import Type


class RelationSetViewSet(viewsets.ModelViewSet):
    queryset = RelationSet.objects.all().order_by('-created')
    serializer_class = RelationSetSerializer

    def list(self, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer_class()

        self.page = self.paginate_queryset(queryset)
        if self.page is not None:
            serializer = self.get_serializer(self.page, many=True)
            return self.get_paginated_response(serializer.data, meta=self.request.query_params.get('meta', False))
        
        relations = serializer(queryset, many=True).data    
        return Response(relations)

    def get_paginated_response(self, data, meta):
        extra = {}
        if meta:
            projects = TextCollection.objects.all()
            users = VogonUser.objects.all()
            extra = {
                'projects': ProjectSerializer(projects, many=True).data,
                'users': UserSerializer(users, many=True).data
            }
        return Response({
            'count':len(self.get_queryset()),
            'results': data,
            **extra
        })
    
    def get_queryset(self, *args, **kwargs):
        queryset = super(RelationSetViewSet, self).get_queryset(*args, **kwargs)
        filtered = RelationSetFilter(self.request.query_params, queryset)
        return filtered.qs

    @action(detail=False, methods=['post'])
    def submit_for_quadriga(self, request):
        relationset_ids = request.data.get('relationset_ids', [])
        relationsets = RelationSet.objects.filter(
            pk__in=relationset_ids,
            createdBy=request.user,
            submitted=False,
        )
        relationsets = [x for x in relationsets if x.ready()]
        
        project_grouper = lambda x: getattr(x.project, 'quadriga_id', -1)
        for project_id, project_group in it.groupby(relationsets, key=project_grouper):
            for text_id, text_group in it.groupby(project_group, key=lambda x: x.occursIn.id):
                text = Text.objects.get(pk=text_id)
                rsets = []
                for rs in text_group:
                    rsets.append(rs.id)
                    rs.save()
                kwargs = {}
                if project_id:
                    kwargs.update({
                        'project_id': project_id
                    })

                submit_relationsets_to_quadriga(rsets, text.id, request.user.id, **kwargs)


        return Response({})

class AnnotationViewSet(viewsets.ViewSet):
    queryset = Text.objects.all()
    def retrieve(self, request, pk=None):
        """
        View to get all data related to annotate text
        """
        file_id = request.query_params.get('file_id', None)
        text = get_object_or_404(Text, pk=pk)
        text.file_id = file_id
        data = {}
        if text.repository.name == "Citesphere":
            repository = text.repository
            manager = repository.manager(request.user)
            file_content = manager.content(file_id)
            try:
                if file_content[0] == "error":
                    return Response(status=file_content[1])
            except Exception:
                pass
            content = file_content
            data['content'] = content
            project_id = request.query_params.get('project_id', None)
            if project_id:
                project = TextCollection.objects.get(pk=project_id)
            else:
                project = request.user.get_default_project()
            data['text'] = text
        else:
            annotator = annotator_factory(request, text)
            data = annotator.render()
            content = data['content'].decode("utf-8")
            data['content'] = content
            project = data['project']

        if project.ownedBy != request.user and request.user not in project.participants.all():
            return Response({
                "error": True,
                "message": "You are not allowed to annotate in this project!"
            }, 403)
        
        data['project'] = project
        appellations = Appellation.objects.filter(
            occursIn=text.id,
            project=project
        )
        dateappellations = DateAppellation.objects.filter(
            occursIn=text.id,
            project=project
        )
        data['dateappellations'] = dateappellations
        data['appellations'] = appellations
        data['relations'] = Relation.objects.filter(
            occursIn=text.id,
        )
        data['relationsets'] = RelationSet.objects.filter(
            occursIn=text.id,
            project=project,
        )
        data['concept_types'] = Type.objects.all()
        relationsets = RelationSet.objects.filter(
            occursIn=text.id,
            project=project,
            submitted=False,
        )
        relationsets = [x for x in relationsets if x.ready()]
        data['pending_relationsets'] = relationsets
        serializer = Text2Serializer(data, context={'request': request})

        # We are overriding `content` variable because of an unknown behavior
        # with Django serializer - `content` flips between string and byte-string
        response = serializer.data
        response['content'] = content
        return Response(response)

    @action(detail=True, methods=['get'], url_name='network')
    def network(self, request, pk=None):
        """
        Provides network data for the graph tab in the text annotation view.
        """
        text = get_object_or_404(Text, pk=pk)
        text.file_id = request.query_params.get('file_id', None)
        annotator = annotator_factory(request, text)
        data = annotator.render()
        project = data['project']

        user = request.user
        relationsets = RelationSet.objects.filter(
            occursIn_id=pk,
            createdBy=user,
            project=project.id
        )
        appellations = Appellation.objects.filter(
            asPredicate=False,
            occursIn_id=pk,
            createdBy=user,
            project=project
        )

        graph = network_data(
            relationsets,
            text_id=pk,
            appellation_queryset=appellations
        )

        return Response(graph)
