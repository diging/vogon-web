"""
Provides project (:class:`.TextCollection`) -related views.
"""

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import login, authenticate
from django.conf import settings 
from django.db.models import Q, Count
from django.core.files.storage import FileSystemStorage
from annotations.models import TextCollection, RelationSet, Appellation, Text, DocumentPosition, ImportTasks
from annotations.forms import ProjectForm, ImportForm
from concepts.models import Concept
import requests

import datetime
import os
import csv
from repository_views import repository_text_content
from repository import auth
from repository.models import Repository
from repository.managers import RepositoryManager
import tempfile
import unicodecsv as csv_unicode
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from annotations.tasks import process_import_task


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
    context = {}
    text_collection = TextCollection.objects.get(id = project_id)
    if request.method == 'POST' and request.user == text_collection.ownedBy:
        data = request.FILES['csv_file']
        # read csv file
        csv_file = csv_unicode.reader(data)
        # Create Temp File.
        name = 'tmp/'+ request.user.username + '_' + str(datetime.datetime.now())+'.csv'
        tmp_file = default_storage.save(name, ContentFile(data.read()))
        # write csv contents to temp file
        with open(tmp_file, 'w') as f:
            writer = csv.writer(f)
            for row in csv_file:
                try:
                    writer.writerow(row)
                except Exception as e:
                    print ('Error in writing row:',e)
        user = request.user
        part_of_id = request.GET.get('part_of')
        action = request.GET.get('action', 'annotate')
       
        import_task = process_import_task.delay(user, project_id, tmp_file, part_of_id, action)
        ImportTasks.objects.create(
            user = request.user,
            task_id = import_task.id,
            file_name = data._name
        )
        return redirect('status')
    return render(request, 'annotations/appellation_upload.html', context)

@login_required
def upload_status(request):
    return render(request, 'annotations/upload_status.html')