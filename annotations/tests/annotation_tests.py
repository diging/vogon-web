import json
from django.urls import reverse

from annotations.utils import VogonAPITestCase
from annotations.models import (
    Text, TextCollection, DocumentPosition, Appellation,
    RelationTemplate, RelationTemplatePart
)
from concepts.models import Concept, Type

class AnnotationCreateRelationTest(VogonAPITestCase):
    def setUp(self):
        super().setUp()
        
        # Create text object
        self.text = Text.objects.create(
            uri='test://uri',
            document_type='PT',
            tokenizedContent='xyz',
            title='test.txt',
            addedBy=self.user,
            content_type='text/plain'
        )

        # Create project object
        self.project = TextCollection.objects.create(
            name='Test project',
            description='Test description',
            ownedBy=self.user
        )
        self.text.partOf.set([self.project])

        # Create concept objects
        self.concept_type = Type.objects.create(
            uri='test://uri',
            label='C1',
            authority='Conceptpower',
            description='test description'
        )
        self.concept = Concept.objects.create(
            uri='test://uri/concept',
            label='Concept',
            authority='Conceptpower',
            description='test description',
            pos='noun',
            typed=self.concept_type
        )

        # Create document positions
        self.position_1 = DocumentPosition.objects.create(
            position_type='CO',
            occursIn=self.text,
            position_value='100,105'
        )
        self.position_2 = DocumentPosition.objects.create(
            position_type='CO',
            occursIn=self.text,
            position_value='320,326'
        )

        # Create appellation
        self.appellation_1 = Appellation.objects.create(
            occursIn=self.text,
            stringRep='appellation',
            startPos=100,
            endPos=105,
            createdBy=self.user,
            interpretation=self.concept,
            project=self.project,
            position=self.position_1
        )
        self.appellation_2 = Appellation.objects.create(
            occursIn=self.text,
            stringRep='xyz',
            startPos=320,
            endPos=326,
            createdBy=self.user,
            interpretation=self.concept,
            project=self.project,
            position=self.position_2
        )

        # Create template
        self.template = RelationTemplate.objects.create(
            createdBy=self.user,
            name='Simple relation',
            description='A simple relation',
            expression='{0s} has a relation {1o}',
            _terminal_nodes='0s,1o'
        )
        self.template_part_1 = RelationTemplatePart.objects.create(
            part_of=self.template,
            internal_id=1,
            source_node_type='CO',
            source_label='Evidence for source relation',
            source_concept=self.concept,
            predicate_node_type='IS',
            object_node_type='TP',
            object_label='relation object',
        )
        self.template_part_2 = RelationTemplatePart.objects.create(
            part_of=self.template,
            internal_id=0,
            source_node_type='TP',
            source_label='Person',
            predicate_node_type='HA',
            object_node_type='RE',
            object_relationtemplate=self.template_part_1,
            object_relationtemplate_internal_id=1
        )


    def test_create_mixed_relations(self):
        
        response = self.client.get(annotate_url)
        annotations = json.loads(response.content)
        print(annotation)