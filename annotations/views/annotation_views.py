import itertools as it
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action, api_view


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
    
    
@api_view(['GET'])
def  submit_relations(request):
    user = VogonUser.objects.get(
            username="sudheerad9"
        )
    # token = RefreshToken.for_user(user)
    # api_authentication()
    text = Text.objects.get(
            uri='test://uri',
            document_type='PT',
            tokenizedContent='xyz',
            title='test.txt',
            addedBy=user,
            content_type='text/plain'
        )

        # Create project object
    project = TextCollection.objects.filter(
        name='Test project',
        description='Test description',
        ownedBy=user,
        createdBy=user
    )[0]
    text.partOf.set([project])

    # Create concept objects
    concept_type = Type.objects.get(
        uri='test://uri',
        label='C1',
        authority='Conceptpower',
        description='test description'
    )
    concept = Concept.objects.get(
        uri='test://uri/concept',
        label='Concept',
        authority='Conceptpower',
        description='test description',
        pos='noun',
        typed=concept_type
    )

    # Create document positions
    position_1 = DocumentPosition.objects.create(
        position_type='CO',
        occursIn=text,
        position_value='100,105'
    )
    position_2 = DocumentPosition.objects.create(
        position_type='CO',
        occursIn=text,
        position_value='320,326'
    )

    # Create appellation
    appellation_1 = Appellation.objects.create(
        occursIn=text,
        stringRep='appellation',
        startPos=100,
        endPos=105,
        createdBy=user,
        interpretation=concept,
        project=project,
        position=position_1
    )
    appellation_2 = Appellation.objects.create(
        occursIn=text,
        stringRep='xyz',
        startPos=320,
        endPos=326,
        createdBy=user,
        interpretation=concept,
        project=project,
        position=position_2
    )
    
    relationset = RelationSet.objects.create(
                project=project,
                createdBy=user,
                occursIn=text
            )

    # Create template
    template = RelationTemplate.objects.create(
        createdBy=user,
        name='Simple relation',
        description='A simple relation',
        expression='{0s} has a relation {1o}',
        _terminal_nodes='0s,1o'
    )
    template_part_1 = RelationTemplatePart.objects.create(
        part_of=template,
        internal_id=1,
        source_node_type='CO',
        source_label='Evidence for source relation',
        source_concept=concept,
        predicate_node_type='IS',
        object_node_type='TP',
        object_label='relation object',
    )
    template_part_2 = RelationTemplatePart.objects.create(
        part_of=template,
        internal_id=0,
        source_node_type='TP',
        source_label='Person',
        predicate_node_type='HA',
        object_node_type='RE',
        object_relationtemplate=template_part_1,
        object_relationtemplate_internal_id=1
    )
    # template = request.data.get(template')
    relation_sets =  RelationSet.objects.get(template=template)
    relations = Relation.objects.filter(part_of__in=relation_sets)
    appellations = Appellation.objects.filter(Relations=relations)
    self.url = self.view.reverse_action(
            'createrelation',
            kwargs={ 'pk': self.template.id }
        )
        payload = {
            "occursIn": self.text.id,
            "project": self.project.id,
            "fields": [
                {
                    "type": "CO",
                    "part_id": self.template_part_1.id,
                    "part_field": "source",
                    "position": {
                        "occursIn_id": self.text.id,
                        "position_type": "CO",
                        "position_value": "150,165"
                    },
                    "data": {
                        "tokenIds": None,
                        "stringRep": "some repr in text"
                    }
                },
                {
                    "type": "TP",
                    "part_id": self.template_part_1.id,
                    "part_field": "object",
                    "appellation": {
                        "id": self.appellation_1.id,
                        "position": {
                            "id": self.position_1.id,
                            "position_type": "CO",
                            "position_value": "100,105",
                            "occursIn": self.text.id,
                            "startOffset": 100,
                            "endOffset": 105
                        },
                        "tokenIds": "",
                        "stringRep": "appellation",
                        "occursIn": {
                            "id": self.text.id
                        },
                        "interpretation": {
                            "id": self.concept.id
                        },
                        "createdBy": {
                            "id": self.user.id
                        },
                        "visible": True,
                        "startPos": 100,
                        "endPos": 105
                    }
                },
                {
                    "type": "TP",
                    "part_id": self.template_part_2.id,
                    "part_field": "source",
                    "appellation": {
                        "id": self.appellation_2.id,
                        "position": {
                            "id": self.position_2.id,
                            "position_type": "CO",
                            "position_value": "320,326",
                            "occursIn": self.text.id,
                            "startOffset": 320,
                            "endOffset": 326
                        },
                        "tokenIds": "",
                        "stringRep": "appellation",
                        "occursIn": {
                            "id": self.text.id
                        },
                        "interpretation": {
                            "id": self.concept.id
                        },
                        "createdBy": {
                            "id": self.user.id
                        },
                        "visible": True,
                        "startPos": 320,
                        "endPos": 326
                    }
                }
            ]
        }
        
        response = self.client.post(self.url, payload)
        result = json.loads(response.content)
        relationset_id = result['relationset_id']
        relationset = RelationSet.objects.get(pk=relationset_id)
        
        self.assertEqual(relationset.template.id, self.template.id)
        self.assertEqual(relationset.project.id, self.project.id)
        self.assertEqual(relationset.occursIn.id, self.text.id)

        relations = Relation.objects.all()
        self.assertEqual(relations.count(), 2)

        relation_1, relation_2 = relations[0], relations[1]
        self.assertEqual(relation_1.part_of.id, relationset.id)
        self.assertEqual(relation_2.part_of.id, relationset.id)


class RelationTemplateCreateUpdateTemplateTest(VogonAPITestCase):
    url = reverse("vogon_rest:relationtemplate-list")

    def setUp(self):
        super().setUp()
        self.test_concept_type_1 = Type.objects.create(
            uri='test://uri_1',
            label='C1',
            authority='Conceptpower',
            description='test description'
        )
        self.test_concept_type_2 = Type.objects.create(
            uri='test://uri_2',
            label='C1',
            authority='Conceptpower',
            description='test description'
        )
        self.test_concept_1 = Concept.objects.create(
            uri='test://uri/concept_1',
            label='Concept 1',
            authority='Conceptpower',
            description='test description 1',
            pos='noun',
        )
        self.template_part_1 = {
            "internal_id": 0,
            "source_node_type": "TP",
            "source_label": "F1",
            "source_description": "F1 description",
            "source_prompt_text": False,
            "source_type": self.test_concept_type_1.id,
            "source_concept": None,
            "source_relationtemplate_internal_id": -1,
            "predicate_node_type": "CO",
            "predicate_label": "F2",
            "predicate_description": "F2 descr",
            "predicate_prompt_text": True,
            "predicate_type": None,
            "predicate_concept": {
                "alt_id": self.test_concept_1.id,
                "uri": "test://uri/concept_1"
            },
            "object_node_type": "TP",
            "object_label": "F3",
            "object_description": "F3 desc",
            "object_prompt_text": False,
            "object_type": self.test_concept_type_2.id,
            "object_concept": None,
            "object_relationtemplate_internal_id": -1
        }

    return Response(status="ok")
    
