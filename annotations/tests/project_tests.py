import json
import mock
from django.urls import reverse

from annotations.models import TextCollection, Text, RelationSet
from annotations.utils import VogonAPITestCase
from annotations.views.project_views import ProjectViewSet
from repository.models import Repository
from util.config import REPO_CONFIG

from rest_framework.viewsets import ViewSet

class ProjectListViewTestCase(VogonAPITestCase):
    url = reverse("vogon_rest:project-list")

    def test_list_empty(self):
        response = self.client.get(self.url)
        result = json.loads(response.content)
        self.assertEqual(result['count'], 0)
        self.assertEqual(len(result['results']), 0)

    def test_single_project(self):
        TextCollection.objects.create(
            name='Test project',
            description='Test project description',
            ownedBy=self.user
        )
        response = self.client.get(self.url)
        projects = json.loads(response.content)['results']
        self.assertEqual(len(projects), 1)

        project = projects[0]
        self.assertEqual(project['name'], 'Test project')

    def test_multiple_projects(self):
        for i in range(10):
            TextCollection.objects.create(
                name=f'Test project {i}',
                description=f'Test project description {i}',
                ownedBy=self.user
            )
        response = self.client.get(self.url)
        projects = json.loads(response.content)['results']
        self.assertEqual(len(projects), TextCollection.objects.count())


class ProjectRetrieveTestCase(VogonAPITestCase):
    def get_url(self, project):
        return reverse(
            "vogon_rest:project-detail",
            kwargs={'pk': project.id}
        )

    def test_project_retrieve(self):
        test_project = TextCollection.objects.create(
            name='Test project',
            description='Test project description',
            ownedBy=self.user
        )
        self.url = self.get_url(test_project)
        response = self.client.get(self.url)
        project = json.loads(response.content)

        self.assertEqual(test_project.name, project['name'])
        self.assertEqual(project['num_texts'], 0)
        self.assertEqual(project['num_relations'], 0)

    def test_project_retrieve_with_texts_relations(self):
        test_project = TextCollection.objects.create(
            name='Test project',
            description='Test project description',
            ownedBy=self.user
        )
        for i in range(3):
            text = Text.objects.create(
                title=f"Test text {i}",
                uri=f'test://uri{i}',
                addedBy=self.user,
            )
            text.partOf.set([test_project])

        for i in range(4):
            text = Text.objects.create(
                title=f"Test text {i}",
                uri=f'test://uri_new{i}',
                addedBy=self.user,
            )
            text.partOf.set([test_project])
            relationset = RelationSet.objects.create(
                project=test_project,
                createdBy=self.user,
                occursIn=text
            )

        self.url = self.get_url(test_project)
        response = self.client.get(self.url)
        project = json.loads(response.content)

        self.assertEqual(project['num_texts'], 7)
        self.assertEqual(project['num_relations'], 4)


class ProjectCreateTestCase(VogonAPITestCase):
    url = reverse("vogon_rest:project-list")

    def test_project_create(self):
        test_project = {
            'name': 'Test project',
            'description': 'Test description',
            'quadriga_id': '1'
        }
        response = self.client.post(self.url, test_project)
        self.assertEqual(response.status_code, 201)

        result = json.loads(response.content)

        project = TextCollection.objects.get(pk=result['id'])
        self.assertEqual(project.id, result['id'])
        self.assertEqual(project.name, test_project['name'])
        self.assertEqual(project.description, test_project['description'])
        self.assertEqual(project.quadriga_id, test_project['quadriga_id'])

from repository.managers import RepositoryManager

class ProjectAddTextTestCase(VogonAPITestCase):
    view = ProjectViewSet()
    view.request = None
    view.basename = "vogon_rest:project"

    class Manager:
        def __init__(cls, **kwargs):
            print('kwargs', kwargs)
            print('here')
        def resource(cls):
            return {
                'title': 'Test Text',
                'created': 'xyz',
                'uri': 'test://uri'
            }

    @mock.patch('repository.managers.RepositoryManager', autospec=True)
    def test_project_add_text(self, mock_manager):
        test_project = TextCollection.objects.create(
            name='Test project',
            description='Test project description',
            ownedBy=self.user
        )
        test_repo = Repository.objects.create(
            name='Test Repo',
            configuration=str(REPO_CONFIG),
            description='Test description'
        )
        text = Text.objects.create(
            title="Test text",
            uri='test://uri',
            addedBy=self.user,
        )
        self.url = self.view.reverse_action('addtext', args=[test_project.id])
        payload = {
            'repository_id': test_repo.id,
            'text_id': text.id
        }

        # ToDo: Figure out mocking and complete the test
        #response = self.client.post(self.url, payload)


class ConceptListViewTest(VogonAPITestCase):
    def setUp(self):
        user = self.user

    def test_concept_empty(self):
        self.url = reverse("vogon_rest:title", args=[test_project.id])
        text, _ = Text.objects.get_or_create(uri=resource.get('uri'),
            defaults=defaults)
        project.texts.add(text)

        serializer = ProjectSerializer(project)