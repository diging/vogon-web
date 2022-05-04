import urllib3.request
import itertools as it
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from django.contrib.contenttypes.models import ContentType

from annotations.models import DocumentPosition, Relation, Appellation, RelationTemplate, RelationTemplatePart, VogonUser, Text, RelationSet, TextCollection, Repository, DateAppellation
from annotations.annotators import annotator_factory
from annotations.serializers import (RelationSetSerializer,
    ProjectSerializer, UserSerializer, Text2Serializer)
from annotations.filters import RelationSetFilter
from annotations.tasks import submit_relationsets_to_quadriga
from annotations.network import network_data
from annotations.views.relationtemplate_views import RelationTemplateViewSet
from concepts.models import Concept, Type


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
        text = get_object_or_404(Text, pk=pk)
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
    
@api_view(['POST'])
def  submit_relations(request):
    meta_data = request.data
    template = request.data.pop('template', None)
    context = meta_data["context"]
    context["creator"] = request.user.username
    meta_data['context'] = context
    relation_sets =  RelationSet.objects.filter(template=template)
    relations = Relation.objects.filter(part_of__in=relation_sets)
    relation_appelation_mapping = {}
    object_id_mapping = {}
    edges_mapping = []
    i = -1
    nodes_mapping = {}
    node_data = {
			     "label": "",
			     "metadata": {
			          "type": "",
    			      "interpretation": "",
    			      "termParts": [
    			           {
    			             "position": "",
    			             "expression": "",
    			             "normalization": "",
    			             "formattedPointer": "",
    			             "format": ""
    			           }
    			      ]
			     },
			     "context":meta_data['context']	
			}
    node_data_copy = node_data
    node_data_relation = {
			     "label": "",
			     "metadata": {
			          "type": "",
			     },
			     "context":meta_data['context']	
			}
    appellation_type = "appellation"
    for relation in relations:
        if relation.source_content_type:
            if relation.source_content_object in object_id_mapping:
                x = object_id_mapping[relation.source_content_object]
            else:
                i+=1
                object_id_mapping[relation.source_content_object] = i
                x = i
            print("hereeeeeeeeeee",(relation.source_content_object.stringRep))
            if relation.source_content_type.model == appellation_type:
                node_data = node_data_copy
                node_data["label"] = relation.source_content_object.stringRep
                node_data["metadata"]["type"] = "appellation_event"
                node_data["metadata"]["interpretation"] = relation.source_content_object.interpretation.uri
                if relation.source_content_object.position:
                    position = relation.source_content_object.position.position_value
                else:
                    position = ""
                node_data["metadata"]["termParts"][0]["position"] = position
                print("hereeeeeeeeeee",(relation.source_content_object.stringRep))

                node_data["metadata"]["termParts"][0]["expression"] = relation.source_content_object.stringRep
                nodes_mapping[str(x)] = node_data
            else:
                node_data_relation["label"] = ""
                node_data_relation["metadata"]["type"] = "relation_event"
                nodes_mapping[str(x)] = node_data_relation
                
        if relation.object_content_type:
            if relation.object_content_object in object_id_mapping:
                y = object_id_mapping[relation.object_content_object]
            else:
                i+=1
                object_id_mapping[relation.object_content_object] = i
                y = i
            if relation.object_content_type.model == appellation_type:
                node_data = node_data_copy
                node_data["label"] = relation.object_content_object.stringRep
                node_data["metadata"]["type"] = "appellation_event"
                node_data["metadata"]["interpretation"] = relation.object_content_object.interpretation.uri
                if relation.object_content_object.position:
                    position = relation.object_content_object.position.position_value
                else:
                    position = ""
                node_data["metadata"]["termParts"][0]["position"] = relation.object_content_object.position.position_value
                node_data["metadata"]["termParts"][0]["expression"] = relation.object_content_object.stringRep
                nodes_mapping[str(y)] = node_data
            else:
                node_data_relation["label"] = ""
                node_data_relation["metadata"]["type"] = "relation_event"
                nodes_mapping[str(y)] = node_data_relation

        if relation.predicate:
            node_data = node_data_copy
            node_data["metadata"]["type"] = "appellation_event"
            node_data["label"] = relation.predicate.stringRep
            node_data["metadata"]["interpretation"] = relation.predicate.interpretation.uri
            position = relation.predicate.position
            if position:
                node_data["metadata"]["termParts"][0]["position"] = position.get('position_value')
            node_data["metadata"]["termParts"][0]["expression"] = relation.predicate.stringRep
            if relation.predicate in object_id_mapping:
                z = object_id_mapping[relation.predicate]
            else:
                i+=1
                object_id_mapping[relation.predicate] = i
                z = i
            nodes_mapping[str(z)] = node_data
        if relation in object_id_mapping:
            k = object_id_mapping[relation]
        else:
            i+=1
            object_id_mapping[relation] = i
            k = i
        node_data_relation["label"] = ""
        node_data_relation["metadata"]["type"] = "relation_event"
        nodes_mapping[str(k)] = node_data_relation
        relation_appelation_mapping[relation.id] = [relation.source_content_object.id, relation.object_content_object.id, relation.predicate.id]
        edges_mapping.append({"source" : k, "relation": "source", "target": x})
        edges_mapping.append({"source" :  k, "relation": "object", "target": y})
        edges_mapping.append({"source" : k, "relation": "predicate", "target": z})
        print(relation_appelation_mapping)   
    result = {}
    result["graph"] = {}
    result["graph"]["metadata"] = meta_data
    result["graph"]["nodes"] = nodes_mapping
    result["graph"]["edges"] = edges_mapping
    return Response(data=result)
