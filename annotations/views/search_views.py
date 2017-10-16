"""
Provides search views.
"""

from django.http import HttpResponse

# from haystack.generic_views import SearchView, FacetedSearchView
# from haystack.query import SearchQuerySet

from annotations.models import Text
from concepts.models import Concept

import json


# class TextSearchView(FacetedSearchView):
#     """Class based view for thread-safe search."""
#     facet_fields = ['collections']
#     template_name = 'annotations/list_texts.html'
#     queryset = SearchQuerySet().models(Text)
#     results_per_page = 20
#
#     def get_context_data(self, *args, **kwargs):
#         """
#         Return context data.
#         """
#         context = super(TextSearchView, self).get_context_data(*args, **kwargs)
#         sort_base = self.request.get_full_path().split('?')[0]
#         if 'query' in context and context['query']:
#             sort_base += '?q=' + context['query']
#
#         context.update({'sort_base': sort_base,})
#         return context
#
#     def form_valid(self, form):
#         order_by = self.request.GET.get('order_by', 'title')
#
#         # If there is no query, just show all of the texts.
#         q = form.cleaned_data.get(self.search_field)
#         query_for_display = q
#         if not q:
#             q = '*'
#             query_for_display = ''
#         form.cleaned_data[self.search_field] = q
#
#         self.queryset = form.search().order_by(order_by)
#         queryset = self.queryset
#         # else:
#         #     params = self.request.GET.getlist('selected_facets')
#         #     queryset = self.get_queryset().order_by(order_by)
#
#         context = self.get_context_data(**{
#             self.form_name: form,
#             'query': query_for_display, #form.cleaned_data.get(self.search_field),
#             'object_list': queryset,
#             'order_by': order_by,
#         })
#
#         return self.render_to_response(context)
#
#     def form_invalid(self, form):
#         """
#         Just return all of the texts.
#         """
#
#         order_by = self.request.GET.get('order_by', 'title')
#         sqs = self.get_queryset()
#
#         # Facet the hell out of those texts.
#         self.selected_facets = self.request.GET.getlist('selected_facets', [])
#         for facet in self.selected_facets:
#             if ":" not in facet:
#                 continue
#             field, value = facet.split(":", 1)
#             if value:
#                 sqs = sqs.narrow(u'%s:"%s"' % (field, sqs.query.clean(value)))
#
#         context = self.get_context_data(**{
#             self.form_name: form,
#             'query': '',
#             'object_list': sqs.order_by(order_by),
#             'order_by': order_by,
#
#         })
#         # Goddammit.
#         context.update({'facets': sqs.facet_counts()})
#         return self.render_to_response(context)
#
#
def concept_autocomplete(request):
    """
    Provides the :class:`.Concept` autocomplete in the home view.
    """
    query = request.GET.get('q', '')
    
    if not query:
        suggestions = []
    else:
        sqs = SearchQuerySet().models(Concept).filter(label__icontains=query.lower())[:20]
        suggestions = [{
            'label': result.label.title(),
            'id': result.id,
            'type': result.typed,
            'description': result.description,
            'uri': result.uri
        } for result in sqs]

    # TODO: can we use the built-in Django JsonResponse for this?
    response_data = json.dumps({'results': suggestions})
    return HttpResponse(response_data, content_type='application/json')
