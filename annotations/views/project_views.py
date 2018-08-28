"""
Provides project (:class:`.TextCollection`) -related views.
"""

from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import login, authenticate
from django.conf import settings
from django.db.models import Q, Count
from django.core.files.storage import FileSystemStorage
from annotations.models import TextCollection, RelationSet, Appellation, Text, DocumentPosition
from annotations.forms import ProjectForm, PathForm
from concepts.models import Concept
import unicodecsv as csv
import io
import requests
from repository_views import repository_text_content
from repository import auth
from repository.models import Repository
from repository.managers import RepositoryManager
import tempfile

def view_project(request, project_id):
    """
    Shows details about a specific project owned by the current user.

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`
    project_id : int

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """

    project = get_object_or_404(TextCollection, pk=project_id)
    template = "annotations/project_details.html"
    request.session['project'] = project.id

    order_by = request.GET.get('order_by', 'title')
    texts = project.texts.all().order_by(order_by)\
                         .values('id', 'title', 'added', 'repository_id', 'repository_source_id')

    paginator = Paginator(texts, 15)
    page = request.GET.get('page')
    try:
        texts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        texts = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        texts = paginator.page(paginator.num_pages)

    from annotations.filters import RelationSetFilter

    # for now let's remove this; it takes long to load the pages and there is a bug somewhere
    # that throws an error sometimes [VGNWB-215]
    #filtered = RelationSetFilter({'project': project.id}, queryset=RelationSet.objects.all())
    #relations = filtered.qs

    context = {
        'user': request.user,
        'title': project.name,
        'project': project,
        'texts': texts,
        #'relations': relations,
    }

    return render(request, template, context)


@login_required
def edit_project(request, project_id):
    """
    Allow the owner of a project to edit it.

    Parameters
    ----------
    project_id : int
    request : `django.http.requests.HttpRequest`

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """
    template = "annotations/project_change.html"
    project = get_object_or_404(TextCollection, pk=project_id)
    if project.ownedBy.id != request.user.id:
        raise PermissionDenied("Whoops, you're not supposed to be here!")

    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            redirect_target = reverse('view_project', args=(project.id,))
            return HttpResponseRedirect(redirect_target)
        else:
            print form.errors
    else:
        form = ProjectForm(instance=project)

    context = {
        'user': request.user,
        'title': 'Editing project: %s' % project.name,
        'project': project,
        'form': form,
        'page_title': 'Edit project'
    }
    return render(request, template, context)


@login_required
def create_project(request):
    """
    Create a new project owned by the current (logged-in) user.

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """
    template = "annotations/project_change.html"

    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.ownedBy = request.user
            project.save()
            redirect_target = reverse('view_project', args=(project.id,))
            return HttpResponseRedirect(redirect_target)
        else:
            print form.errors
    else:
        form = ProjectForm()

    context = {
        'user': request.user,
        'title': 'Create a new project',
        'form': form,
        'page_title': 'Create a new project'
    }
    return render(request, template, context)


def list_projects(request):
    """
    All known projects.

    Parameters
    ----------
    project_id : int
    request : `django.http.requests.HttpRequest`

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """

    fields = [
        'id',
        'name',
        'created',
        'ownedBy__id',
        'ownedBy__username',
        'description',
        'num_texts',
        'num_relations',
    ]
    qs = TextCollection.objects.all()
    qs = qs.annotate(num_texts=Count('texts'),
                     num_relations=Count('texts__relationsets'))
    qs = qs.values(*fields)

    template = "annotations/project_list.html"
    context = {
        'user': request.user,
        'title': 'Projects',
        'projects': qs,
    }
    return render(request, template, context)


@login_required
def import_appellation(request, project_id):
    print("TEST")
    def add_text_to_project(request, repository_id, text_id, project_id):
        repository = get_object_or_404(Repository, pk=repository_id)
        project = get_object_or_404(TextCollection, pk=project_id)

        manager = RepositoryManager(repository.configuration, user=request.user)
        try:
            resource = manager.resource(id=int(text_id))
        except IOError:
            return render(request, 'annotations/repository_ioerror.html', {}, status=500)
        defaults = {
            'title': resource.get('title'),
            'created': resource.get('created'),
            'repository': repository,
            'repository_source_id': text_id,
            'addedBy': request.user,
        }
        text, _ = Text.objects.get_or_create(uri=resource.get('uri'),  defaults=defaults)
        project.texts.add(text)

    context = {}

    text_collection = TextCollection.objects.get(id = project_id)
    if request.method == 'POST' and request.user == text_collection.ownedBy:
        csv_file = request.FILES['csv_file']
        csv_reader = csv.DictReader(csv_file, encoding='utf-8')
        csv_reader.next()

        handle, fn = tempfile.mkstemp(suffix='.csv')
        csv_file_path = '/Users/taylorquinn/Desktop/1522.csv'
        with open(csv_file_path, 'rt') as csvfile:
            annotations = csv.reader(csvfile, delimiter=' ', quotechar='|')
            with os.fdopen(handle,"w", encoding='utf8',errors='surrogateescape', newline='') as f:
                writer=csv.writer(f)
                for row in annotations:
                    try:
                        writer.writerow(row)
                    except Exception as e:
                        print ('Error in writing row:',e)
        for row in csv_reader:
            try:
                parent = Text.objects.get(uri=row[3])
                text = Text.objects.get(part_of_id=parent.id)
                occur = text
            except:
                url = "https://amphora.asu.edu/amphora/resource/get?uri=" + row[3] + "&format=json"
                text_request = requests.get(url, headers=auth.jars_github_auth(request.user))
                text_json = text_request.json()
                found = False
                while found == False:
                    for content in text_json['content']:
                        if content['content_resource']['content_type'] == 'text/plain':
                            text_content = content['content_resource']['id']
                            found = True
                add_text_to_project(request, 1, text_json['id'],project_id)
                text = Text.objects.get(uri=row[3])
                repository_text_content(request, 1, text_json['id'], text_content)
                occur = Text.objects.get(part_of_id=text.id)

    return render(request, 'annotations/appellation_upload.html', context)

