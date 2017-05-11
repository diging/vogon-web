import requests
from django.shortcuts import get_object_or_404, render
from django.http import Http404
from annotations.tasks import tokenize
from annotations.utils import basepath
from annotations.models import TextCollection, VogonUserDefaultProject


class Annotator(object):
    template = ''
    content_types = []

    def __init__(self, request, text):
        project_id = request.GET.get('project_id')
        if project_id:
            project = TextCollection.objects.get(pk=project_id)
        else:
            project = request.user.get_default_project()

        project.texts.add(text)
        self.project = project;
        self.context = {
            'request': request,
            'user': request.user,
        }
        self.text = text

    def get_content(self):
        """
        """
        raise NotImplementedError('get_content must be defined by a subclass')

    def render(self, context={}):
        context.update(self.get_context())
        return render(self.context.get('request'), self.template, context)

    def render_display(self, context={}):
        if not hasattr(self, 'display_template'):
            raise Http404('No display renderer for this format.')
        context.update(self.get_context())
        return render(self.context.get('request'), self.display_template, context)


class PlainTextAnnotator(Annotator):
    template = 'annotations/vue.html'
    display_template = 'annotations/annotation_display.html'
    content_types = ('text/plain',)

    def get_resource(self):
        if not self.text.repository:
            return
        manager = self.text.repository.manager(self.context['user'])
        return manager.content(id=int(self.text.repository_source_id))


    def get_resource(self):
        manager = self.text.repository.manager(self.context['user'])
        return manager.content(id=int(self.text.repository_source_id))

    def get_content(self, resource):

        response = requests.get(resource.get('location'))
        if response.status_code == requests.codes.OK:
            return response.content
        return

    def get_context(self):
        resource = self.get_resource()
        request = self.context.get('request')
        return {
            'text': self.text,
            'textid': self.text.id,
            'title': 'Annotate Text',
            'content': self.get_content(resource),
            'baselocation' : basepath(request),
            'userid': request.user.id,
            'title': self.text.title,
            'next': resource.get('next'),
            'next_content': resource.get('next_content'),
            'previous': resource.get('previous'),
            'previous_content': resource.get('previous_content'),
            # 'source_id': resource.id,
            'repository_id': self.text.repository.id,
            'project': self.project
        }


class DigiLibImageAnnotator(Annotator):
    """
    Content is loaded dynamically through a digilib gateway (e.g. Giles).
    """
    template = 'annotations/annotate_image.html'
    content_types = ('image/gif', 'image/png', 'image/jpeg', 'image/jpg'
                     'image/bmp', 'image/tiff', 'image/x-tiff',)


    def get_resource(self):
        if not self.text.repository:
            return
        manager = self.text.repository.manager(self.context['user'])
        return manager.content(id=int(self.text.repository_source_id))

    def get_content(self, resource):
        """
        The javascript controller in the template will use the content location
        to make requests for specific regions of the image.
        """

        # parent_id = resource.data.get('content_for')
        return resource.get('location')

    def get_context(self):
        resource = self.get_resource()

        return {
            'textid': self.text.id,
            'userid': self.context.get('request').user.id,
            'text': self.text,
            'location': self.get_content(resource),
            'next': resource.get('next'),
            'next_content': resource.get('next_content'),
            'previous': resource.get('previous'),
            'previous_content': resource.get('previous_content'),
            'source_id': self.text.repository_source_id,
            'repository_id': self.text.repository.id,
            'project': self.project
        }


# TODO: implement this!
class WebAnnotator(Annotator):
    """
    For annotating rendered hypertext content.
    """
    pass


ANNOTATORS = (
    PlainTextAnnotator,
    DigiLibImageAnnotator,
    WebAnnotator
)


def annotator_factory(request, text):
    """
    Find and instantiate an annotator for a :class:`.Text`\.
    """
    for annotator in ANNOTATORS:
        if text.content_type in annotator.content_types:
            return annotator(request, text)
    return


def annotator_exists(content_type):
    for annotator in ANNOTATORS:
        if content_type in annotator.content_types:
            return True
    return False
