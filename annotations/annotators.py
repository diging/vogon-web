"""
This module provides annotation functionality using a rough approximation of a
factory pattern.

To load an annotator for a :class:`annotations.models.Text` instance, use
:func:`.annotator_factory` in this module. This will return an instance of a
subclass of :class:`.Annotator`\, whose ``render()`` method can be used to
directly generate a response in a view.

For example:

.. code-block:: python

   from annotations.annotators import annotator_factory
   from annotations.models import Text

   def my_view(request, text_id):
       \"\"\"My annotation view!\"\"\"
       text = Text.object.get(pk=text_id)
       annotator = annotator_factory(request, text)
       return annotator.render()


To create a new annotator (e.g. to support annotation of a new content type),
implement a subclass of :class:`.Annotator`\. Each annotator must...

1. Implement the instance method :meth:`Annotator.get_content`\. It should
   accept one parameter (``resource`` in the base method), a dict containing
   information about the resource retrieved from the
   :class:`repository.models.Repository` associated with the current
   :class:`annotations.models.Text`. The specific data provided in this dict
   depends on the configuration of the repository.
2. Specify the static property ``template``. This should be a ``str`` indicating
   the relative path of the HTML template for this annotator.
3. Specify the static property ``content_types``. This should be a list of
   ``str`` MIME types that this annotator handles.
4. Be registered in ``ANNOTATORS``, below. If more than one annotator supports
   a particular content type, the order in which those annotators appear in
   ``ANNOTATORS`` will dictate their priority.

You may also provide the static property ``display_template``, which will be
used to generate a read-only view for annotations.

The template (and its attendant client-side application, if there is one) should
use the REST endpoints provided by :mod:`annotations.views.rest_views` to create
:class:`annotations.models.Appellation`\, and
:class:`annotations.models.DateAppellation` instances. The REST views provided
by :mod:`annotations.views.relationtemplate_views` should be used to generate
:class:`.RelationSet` instances.

"""


import requests
from django.shortcuts import get_object_or_404, render
from django.http import Http404
from annotations.tasks import tokenize
from annotations.utils import basepath
from annotations.models import TextCollection, VogonUserDefaultProject
from urlparse import urlparse
import chardet


class Annotator(object):
    """
    Base class for annotators.
    """
    template = ''
    content_types = []

    def __init__(self, request, text):
        project_id = request.GET.get('project_id')
        if project_id:
            project = TextCollection.objects.get(pk=project_id)
        else:
            project = request.user.get_default_project()

        self.project = project;
        self.context = {
            'request': request,
            'user': request.user,
        }
        self.text = text
        self.resource = None

    def get_content(self, resource):
        """
        This method should be implemented in a subclass.

        Parameters
        ----------
        resource : dict
            Data from the selected text's repository.

        Return
        ------
        object
        """
        raise NotImplementedError('Must be implemented in a subclass')

    def get_resource(self):
        """
        Retrieve the resource represented by our :class:`.Text` instance.
        """
        if self.resource is not None:
            return self.resource
        if not self.text.repository:
            return
        manager = self.text.repository.manager(self.context['user'])
        self.resource = manager.content(id=int(self.text.repository_source_id))
        return self.resource

    def render(self, context={}):
        """
        Render this annotator's template to a response.

        Parameters
        ----------
        context : dict
            Extra context to be passed to :func:`django.shortcuts.render`\.
            Note that keys that conflict with the return value of
            :meth:`.get_context` will be overridden.

        Returns
        -------
        :class:`django.http.response.HttpResponse`
        """
        context.update(self.get_context())
        return render(self.context.get('request'), self.template, context)

    def render_display(self, context={}):
        """
        Render this annotator's display template to a response.

        If :prop:`.display_template` is not set, will raise
        :class:`django.http.Http404`\.

        Parameters
        ----------
        context : dict
            Extra context to be passed to :func:`django.shortcuts.render`\.
            Note that keys that conflict with the return value of
            :meth:`.get_context` will be overridden.

        Returns
        -------
        :class:`django.http.response.HttpResponse`
        """
        if not hasattr(self, 'display_template'):
            raise Http404('No display renderer for this format.')
        context.update(self.get_context())
        return render(self.context.get('request'), self.display_template, context)

    def get_context(self):
        resource = self.get_resource()
        request = self.context.get('request')
        content = self.get_content(resource)
        detect  = chardet.detect(content)
        return {
            'text': self.text,
            'textid': self.text.id,
            'title': 'Annotate Text',
            'content': content.decode(detect['encoding']).encode('utf-8'), # We are using chardet to guess the encoding becuase giles is returning everyting with a utf-8 header even if it is not utf-8
            'baselocation' : basepath(request),
            'userid': request.user.id,
            'title': self.text.title,
            'repository_id': self.text.repository.id,
            'project': self.project
        }


class PlainTextAnnotator(Annotator):
    """
    Generates index-offset annotations for plain text content.
    """
    template = 'annotations/vue.html'
    display_template = 'annotations/annotation_display.html'
    content_types = ('text/plain',)

    def get_content(self, resource):
        target = resource.get('location')
        request = self.context['request']
        manager = self.text.repository.manager(request.user)
        endpoint = manager.configuration['endpoint']
        if urlparse(target).netloc == urlparse(endpoint).netloc:
            return manager.get_raw(target)
        response = requests.get(target)
        if response.status_code == requests.codes.OK:
            return response.content
        return

    def get_context(self):
        context = super(PlainTextAnnotator, self).get_context()
        context.update({
            'next': self.resource.get('next'),
            'next_content': self.resource.get('next_content'),
            'previous': self.resource.get('previous'),
            'previous_content': self.resource.get('previous_content'),
        })
        return context


class DigiLibImageAnnotator(Annotator):
    """
    Provides bounding-box annotations for images.

    Content is loaded dynamically through a digilib gateway (e.g. Giles).
    """
    template = 'annotations/annotate_image.html'
    content_types = ('image/gif', 'image/png', 'image/jpeg', 'image/jpg',
                     'image/bmp', 'image/tiff', 'image/x-tiff',)

    def get_content(self, resource):
        """
        The javascript controller in the template will use the content location
        to make requests for specific regions of the image.
        """
        # parent_id = resource.data.get('content_for')
        return resource.get('location')

    def get_context(self):
        context = super(DigiLibImageAnnotator, self).get_context()
        context.update({
            'next': self.resource.get('next'),
            'next_content': self.resource.get('next_content'),
            'previous': self.resource.get('previous'),
            'previous_content': self.resource.get('previous_content'),
            'location': context['content'],
            'source_id': self.text.repository_source_id,
        })
        return context

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
    Find and instantiate an annotator for a :class:`.Text` instance.

    Parameters
    ----------
    request : :class:`django.http.request.HttpRequest`
    text : :class:`annotations.models.Text`

    Returns
    -------
    :class:`.Annotator`
        Will be an instance of an :class:`.Annotator` subclass.
    """
    for annotator in ANNOTATORS:
        if text.content_type in annotator.content_types:
            return annotator(request, text)
    return


def supported_content_types():
    """
    Generate a list of MIME types for which we have an annotator.

    Returns
    -------
    list
    """
    return list(set([ctype for annotator in ANNOTATORS
                     for ctype in annotator.content_types]))

def annotator_exists(content_type):
    """
    Check whether or not we have an annotator for a particular content type.

    Parameters
    ----------
    content_type : str
        A MIME type (or, really anything that appears in the ``content_types``)
        property of an Annotator.

    Returns
    -------
    bool
    """
    for annotator in ANNOTATORS:
        if content_type in annotator.content_types:
            return True
    return False
