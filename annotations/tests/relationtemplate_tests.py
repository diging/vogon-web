import json
import copy
from django.urls import reverse

from annotations.utils import VogonAPITestCase
from annotations.models import (
    Text, TextCollection, DocumentPosition, Appellation,
    RelationTemplate, RelationTemplatePart, RelationSet,
    Relation
)
from annotations.views.relationtemplate_views import RelationTemplateViewSet
from concepts.models import Concept, Type

class RelationTemplateListTest(VogonAPITestCase):
    url = reverse("vogon_rest:relationtemplate-list")

    def test_list_empty(self):
        response = self.client.get(self.url)
        result = json.loads(response.content)
        self.assertEqual(len(result), 0)

    def test_multiple_templates(self):
        self.concept = Concept.objects.create(
            uri='test://uri/concept',
            label='Concept',
            authority='Conceptpower',
            description='test description',
            pos='noun',
        )
        for i in range(3):
            template = RelationTemplate.objects.create(
                createdBy=self.user,
                name=f'Simple relation {i}',
                description=f'A simple relation {i}',
                expression='{0s} has a relation {1o}',
                _terminal_nodes='0s,1o'
            )
            template_part_1 = RelationTemplatePart.objects.create(
                part_of=template,
                internal_id=1,
                source_node_type='CO',
                source_label='Evidence for source relation',
                source_concept=self.concept,
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

        response = self.client.get(self.url)
        templates = json.loads(response.content)

        self.assertEqual(len(templates), RelationTemplate.objects.count())
        self.assertEqual(sum([len(x['fields']) for x in templates]), 9)


class RelationTemplateRetrieveTest(VogonAPITestCase):
    def get_url(self, template):
        return reverse(
            "vogon_rest:relationtemplate-detail",
            kwargs={'pk': template.id}
        )

    def test_template_retrieve(self):
        test_concept = Concept.objects.create(
            uri='test://uri/concept',
            label='Concept',
            authority='Conceptpower',
            description='test description',
            pos='noun',
        )
        test_template = RelationTemplate.objects.create(
            createdBy=self.user,
            name='Simple relation',
            description='A simple relation',
            expression='{0s} has a relation {1o}',
            _terminal_nodes='0s,1o'
        )
        test_template_part_1 = RelationTemplatePart.objects.create(
            part_of=test_template,
            internal_id=1,
            source_node_type='CO',
            source_label='Evidence for source relation',
            source_concept=test_concept,
            predicate_node_type='IS',
            object_node_type='TP',
            object_label='relation object',
        )
        test_template_part_2 = RelationTemplatePart.objects.create(
            part_of=test_template,
            internal_id=0,
            source_node_type='TP',
            source_label='Person',
            predicate_node_type='HA',
            object_node_type='RE',
            object_relationtemplate=test_template_part_1,
            object_relationtemplate_internal_id=1
        )

        response = self.client.get(self.get_url(test_template))
        template = json.loads(response.content)

        self.assertEqual(template['id'], test_template.id)


class RelationTemplateCreateRelationTest(VogonAPITestCase):
    view = RelationTemplateViewSet()
    view.request = None
    view.basename = "vogon_rest:relationtemplate"

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

    def test_invalid_template_creation(self):
        payload = {
            "name": "Test relation",
            "description": "Test description",
            "expression": "invalid_expr",
            "terminal_nodes": "0s,1o",
            "parts": [
                self.template_part_1
            ]
        }

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 500)

        result = json.loads(response.content)
        self.assertEqual(result["success"], False)
        self.assertEqual(result["error"], "Invalid expression pattern")

    def test_invalid_terminal_nodes_pattern(self):
        payload = {
            "name": "Test relation",
            "description": "Test description",
            "expression": "invalid_expr",
            "terminal_nodes": "invalid_term",
            "parts": [
                self.template_part_1
            ]
        }

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 500)

        result = json.loads(response.content)
        self.assertEqual(result["success"], False)
        self.assertEqual(result["error"], "Invalid pattern for terminal nodes")

    def test_relation_self_loops(self):
        self.template_part_1_loop = self.template_part_1
        self.template_part_1_loop["object_relationtemplate_internal_id"] = 0
        
        payload = {
            "name": "Test relation",
            "description": "Test description",
            "expression": "{0s} has a relation {1o}",
            "terminal_nodes": "0s,1o",
            "parts": [
                self.template_part_1_loop
            ]
        }

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 500)

        result = json.loads(response.content)
        self.assertEqual(result["success"], False)
        self.assertEqual(result["error"], "Relation structure contains self-loops")

    def test_relation_cyclic(self):
        self.template_part_2 = copy.deepcopy(self.template_part_1)
        self.template_part_1["object_node_type"] = "RE"
        self.template_part_2["object_node_type"] = "RE"
        self.template_part_2["internal_id"] = 1
        self.template_part_2["object_relationtemplate_internal_id"] = 0
        self.template_part_1["object_relationtemplate_internal_id"] = 1

        payload = {
            "name": "Test relation",
            "description": "Test description",
            "expression": "{0s} has a relation {1o}",
            "terminal_nodes": "0s,1o",
            "parts": [
                self.template_part_1,
                self.template_part_2
            ]
        }

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 500)

        result = json.loads(response.content)
        self.assertEqual(result["success"], False)
        self.assertEqual(result["error"], "Relation structure is cyclic or disconnected")

    def test_template_creation_success(self):
        self.template_part_2 = copy.deepcopy(self.template_part_1)

        payload = {
            "name": "Test relation",
            "description": "Test description",
            "expression": "{0s} has a relation {1o}",
            "terminal_nodes": "0s,1o",
            "parts": [
                self.template_part_1,
                self.template_part_2
            ]
        }

        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, 200)

        result = json.loads(response.content)

        # Template should be created
        template = RelationTemplate.objects.get(pk=result["template_id"])
        self.assertEqual(template.name, "Test relation")

        # 2 template parts should be created
        template_parts = RelationTemplatePart.objects.all()
        self.assertEqual(len(template_parts), 2)

        # Template parts should have `part_of` field to be 
        # the created `template`
        self.assertEqual(template_parts[0].part_of.id, template.id)
        self.assertEqual(template_parts[1].part_of.id, template.id)

    def test_template_update_success(self):
        # Create template
        self.template_part_2 = copy.deepcopy(self.template_part_1)
        payload = {
            "name": "Test relation",
            "description": "Test description",
            "expression": "{0s} has a relation {1o}",
            "terminal_nodes": "0s,1o",
            "parts": [
                self.template_part_1,
                self.template_part_2
            ]
        }
        response = self.client.post(self.url, payload)
        template_id = json.loads(response.content)['template_id']
        
        # Update template
        update_url = reverse(
            "vogon_rest:relationtemplate-detail",
            kwargs={'pk': template_id}
        )
        payload["name"] = "Test relation new"
        payload["description"] = "Test description new"
        response = self.client.put(update_url, payload)

        self.assertEqual(response.status_code, 200)

        template = RelationTemplate.objects.get(pk=template_id)
        self.assertEqual(template.name, "Test relation new")
        self.assertEqual(template.description, "Test description new")


class RelationTemplateDeleteTest(VogonAPITestCase):
    def get_url(self, template):
        return reverse(
            "vogon_rest:relationtemplate-detail",
            kwargs={'pk': template.id}
        )

    def setUp(self):
        super().setUp()
        self.test_text = Text.objects.create(
            title="Test text",
            uri='test://uri',
            addedBy=self.user,
        )
        self.test_template = RelationTemplate.objects.create(
            name='Test relation',
            description='Test description',
            expression='{0s}{0p}{0o}',
            _terminal_nodes='0s,1s',
            createdBy=self.user
        )

    def test_delete_template_if_relation_exists(self):
        # If a relation already exists for a template, user is not allowed
        # to delete the template.

        # Create relation associated with the templates
        relation = RelationSet.objects.create(
            template=self.test_template,
            createdBy=self.user,
            occursIn=self.test_text
        )

        response = self.client.delete(self.get_url(self.test_template))
        result = json.loads(response.content)

        self.assertEqual(response.status_code, 500)
        self.assertEqual(result["success"], False)
        self.assertEqual(
            result["error"], 
            "Could not delete relation template because there is data associated with it"
        )

        # Ensure template is not deleted
        template = RelationTemplate.objects.get(pk=self.test_template.id)
        self.assertEqual(template.id, self.test_template.id)

    def test_template_delete_success(self):
        response = self.client.delete(self.get_url(self.test_template))
        result = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(result["success"], True)


class RelationTemplateFormViewTest(VogonAPITestCase):
    view = RelationTemplateViewSet()
    view.request = None
    view.basename = "vogon_rest:relationtemplate"

    def test_create_form_view(self):
        self.url = self.view.reverse_action('createform')

        for i in range(3):
            Type.objects.create(
                uri=f'test://uri_{i}',
                label=f'Label {i}',
                authority='Conceptpower',
                description='Description {i}'
            )
        response = self.client.get(self.url)
        result = json.loads(response.content)

        self.assertEqual(len(result["open_concepts"]), 3)