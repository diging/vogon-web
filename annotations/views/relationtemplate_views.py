"""
Provides :class:`.RelationTemplate`\-related views.
"""

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.forms import formset_factory
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template import RequestContext, loader


from annotations.forms import (RelationTemplatePartFormSet,
                               RelationTemplatePartForm,
                               RelationTemplateForm)
from annotations.models import (RelationTemplate, RelationTemplatePart,
                                RelationSet, Relation, Appellation)
from concepts.models import Concept, Type

import copy
import json
import logging
import networkx as nx

logger = logging.getLogger(__name__)
logger.setLevel('ERROR')


@staff_member_required
def add_relationtemplate(request):
    """
    Staff can use this view to create :class:`.RelationTemplate`\s.

    Parameters
    ----------
    project_id : int
    request : `django.http.requests.HttpRequest`

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """

    # TODO: This could use quite a bit of refactoring, or at least breaking
    #  apart into more manageable bits.

    # Each RelationTemplatePart is a "triple", the subject or object of which
    #  might be another RelationTemplatePart.
    formset = formset_factory(RelationTemplatePartForm,
                              formset=RelationTemplatePartFormSet)
    form_class = RelationTemplateForm   # e.g. Name, Description.

    context = {}
    error = None    # TODO: <-- make this less hacky.
    if request.POST:
        logger.debug('add_relationtemplate: post request')

        # Instatiate both form(set)s with data.
        relationtemplatepart_formset = formset(request.POST, prefix='parts')
        relationtemplate_form = form_class(request.POST)
        context['formset'] = relationtemplatepart_formset
        context['templateform'] = relationtemplate_form

        if all([relationtemplatepart_formset.is_valid(),
                relationtemplate_form.is_valid()]):
            logger.debug('add_relationtemplate: both forms are valid')
            # We commit the RelationTemplate to the database first, so that we
            #  can use it in the FK relation ``RelationTemplatePart.part_of``.
            relationTemplate = relationtemplate_form.save()

            # We index RTPs so that we can fill FK references among them.
            relationTemplateParts = {}
            dependency_order = {}    # Source RTP index -> target RTP index.
            for form in relationtemplatepart_formset:
                relationTemplatePart = RelationTemplatePart()
                relationTemplatePart.part_of = relationTemplate
                relationTemplatePart.internal_id = form.cleaned_data['internal_id']

                # Since many field names are shared for source, predicate, and
                #  object, this approach should cut down on a lot of repetitive
                #  code.
                for part in ['source', 'predicate', 'object']:
                    setattr(relationTemplatePart, part + '_node_type',
                            form.cleaned_data[part + '_node_type'])
                    setattr(relationTemplatePart, part + '_prompt_text',
                            form.cleaned_data[part + '_prompt_text'])
                    setattr(relationTemplatePart, part + '_label',
                            form.cleaned_data[part + '_label'])

                    # Node is a concept Type. e.g. ``E20 Person``.
                    if form.cleaned_data[part + '_node_type'] == 'TP':
                        setattr(relationTemplatePart, part + '_type',
                                form.cleaned_data[part + '_type'])
                        setattr(relationTemplatePart, part + '_description',
                                form.cleaned_data[part + '_description'])

                    # Node is a specific Concept, e.g. ``employ``.
                    elif form.cleaned_data[part + '_node_type'] == 'CO':
                        setattr(relationTemplatePart, part + '_concept',
                                form.cleaned_data[part + '_concept'])
                        # We may still want to provide instructions to the user
                        #  via the description field.
                        setattr(relationTemplatePart, part + '_description',
                                form.cleaned_data[part + '_description'])

                    # Node is another RelationTemplatePart.
                    elif form.cleaned_data[part + '_node_type'] == 'RE':
                        target_id = form.cleaned_data[part + '_relationtemplate_internal_id']
                        setattr(relationTemplatePart,
                                part + '_relationtemplate_internal_id',
                                target_id)
                        if target_id > -1:
                            # This will help us to figure out the order in
                            #  which to save RTPs.
                            dependency_order[relationTemplatePart.internal_id] = target_id

                # Index so that we can fill FK references among RTPs.
                relationTemplateParts[relationTemplatePart.internal_id] = relationTemplatePart

            # If there is interdependency among RTPs, determine and execute
            #  the correct save order.
            if len(dependency_order) > 0:
                # Find the relation template furthest downstream.
                # TODO: is this really better than hitting the database twice?
                start_rtp = copy.deepcopy(dependency_order.keys()[0])
                this_rtp = copy.deepcopy(start_rtp)
                save_order = [this_rtp]
                iteration = 0
                while True:
                    this_rtp = copy.deepcopy(dependency_order[this_rtp])
                    if this_rtp not in save_order:
                        save_order.insert(0, copy.deepcopy(this_rtp))
                    if this_rtp in dependency_order:
                        iteration += 1
                    else:   # Found the downstream relation template.
                        break

                    # Make sure that we're not in an endless loop.
                    # TODO: This is kind of a hacky way to handle the situation.
                    #  Maybe we should move this logic to the validation phase,
                    #  so that we can handle errors in a Django-esque fashion.
                    if iteration > 0 and this_rtp == start_rtp:
                        error = 'Endless loop'
                        break
                if not error:
                    # Resolve internal ids for RTP references into instance pks,
                    #  and populate the RTP _relationtemplate fields.
                    for i in save_order:
                        for part in ['source', 'object']:
                            dep = getattr(relationTemplateParts[i],
                                          part + '_relationtemplate_internal_id')
                            if dep > -1:
                                setattr(relationTemplateParts[i],
                                        part + '_relationtemplate',
                                        relationTemplateParts[dep])
                        # Only save non-committed instances.
                        if not relationTemplateParts[i].id:
                            relationTemplateParts[i].save()

            # Otherwise, just save the (one and only) RTP.
            elif len(relationTemplateParts) == 1:
                relationTemplateParts.values()[0].save()

            if not error:
                # TODO: when the list view for RTs is implemented, we should
                #  direct the user there.
                return HttpResponseRedirect(reverse('list_relationtemplate'))

            else:
                # For now, we can render this view-wide error separately. But
                #  we should probably make this part of the normal validation
                #  process in the future. See comments above.
                context['error'] = error
        else:
            logger.debug('add_relationtemplate: forms not valid')
            context['formset'] = relationtemplatepart_formset
            context['templateform'] = relationtemplate_form

    else:   # No data, start with a fresh formset.
        context['formset'] = formset(prefix='parts')
        context['templateform'] = form_class()

    return render(request, 'annotations/relationtemplate.html', context)


@login_required
def list_relationtemplate(request):
    """
    Returns a list of all :class:`.RelationTemplate`\s.

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """
    queryset = RelationTemplate.objects.all()
    search = request.GET.get('search', None)
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )

    data = {
        'templates': [{
            'id': rt.id,
            'name': rt.name,
            'description': rt.description,
            'fields': rt.fields,
            } for rt in queryset]
        }

    response_format = request.GET.get('format', None)
    if response_format == 'json':
        return JsonResponse(data)

    template = loader.get_template('annotations/relationtemplate_list.html')
    context = RequestContext(request, {
        'user': request.user,
        'data': data,
    })

    return HttpResponse(template.render(context))


@login_required
def get_relationtemplate(request, template_id):
    """
    Returns data on fillable fields in a :class:`.RelationTemplate`\.

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`
    template_id : int

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """

    relation_template = get_object_or_404(RelationTemplate, pk=template_id)

    data = {
        'fields': relation_template.fields,
        'name': relation_template.name,
        'description': relation_template.description,
        'id': template_id,
        'expression': relation_template.expression,
    }
    response_format = request.GET.get('format', None)
    if response_format == 'json':
        return JsonResponse(data)

    template = loader.get_template('annotations/relationtemplate_show.html')
    context = RequestContext(request, {
        'user': request.user,
        'data': data,
    })

    return HttpResponse(template.render(context))


@login_required
def create_from_relationtemplate(request, template_id):
    """
    Create a :class:`.RelationSet` and constituent :class:`.Relation`\s from
    a :class:`.RelationTemplate` and user annotations.

    This is mainly used by the RelationTemplateController in the text
    annotation  view.

    Parameters
    ----------
    request : `django.http.requests.HttpRequest`
    template_id : int

    Returns
    ----------
    :class:`django.http.response.HttpResponse`
    """

    # TODO: this could also use quite a bit of attention in terms of
    #  modularization.

    template = get_object_or_404(RelationTemplate, pk=template_id)

    # Index RelationTemplateParts by ID.
    template_parts = {part.id: part for part in template.template_parts.all()}

    if request.POST:
        relations = {}
        data = json.loads(request.body)

        relation_data = {}
        for field in data['fields']:

            if field['part_id'] not in relation_data:
                relation_data[int(field['part_id'])] = {}
            relation_data[int(field['part_id'])][field['part_field']] = field

        relation_set = RelationSet(
            template=template,
            createdBy=request.user,
            occursIn_id=data['occursIn'],
        )
        relation_set.save()

        def _create_appellation(field_data, template_part, field,
                               evidence_required=True):
            """
            Some fields may have data for appellations that have not yet been
            created. So we do that here.
            """
            node_type = getattr(template_part, '%s_node_type' % field)

            appellation_data = {
                'occursIn_id': data['occursIn'],
                'createdBy_id': request.user.id,
            }
            if evidence_required and field_data:
                # We may be dealing with an image appellation, in which case
                #  we should expect to find position data in the request.
                position_data = field_data.pop('position', None)
                if position_data:
                    position = DocumentPosition.objects.create(**position_data)
                    appellation_data.update({
                        'position': position,
                    })

                # These should be blank instead of null.
                appellation_data.update({
                    'tokenIds': field_data['data'].get('tokenIds', ''),
                    'stringRep': field_data['data'].get('stringRep', ''),
                })
            else:    # TODO: is this necessary?
                appellation_data.update({'asPredicate': True})

            if node_type == RelationTemplatePart.CONCEPT:
                # The interpretation is already provided.
                interpretation = getattr(template_part, '%s_concept' % field)

            # TODO: these should not be hard-coded. Add these URIs to config.
            elif node_type == RelationTemplatePart.TOBE:
                interpretation = Concept.objects.get(uri="http://www.digitalhps.org/concepts/CON3fbc4870-6028-4255-9998-14acf028a316")
            elif node_type == RelationTemplatePart.HAS:
                interpretation = Concept.objects.get(uri="http://www.digitalhps.org/concepts/CON83f5110b-5034-4c95-82f8-8f80ff55a1b9")
            if interpretation:
                appellation_data.update({'interpretation': interpretation})

            if field == 'predicate':
                appellation_data.update({'asPredicate': True})
            appellation = Appellation(**appellation_data)
            appellation.save()
            return appellation

        relation_dependency_graph = nx.DiGraph()


        # Since we don't know anything about the structure of the
        #  RelationTemplate, we watch for nodes that expect to be Relation
        #  instances and recurse to create them as needed. We store the results
        #  for each Relation in ``relation_data_processed`` so that we don't
        #  create duplicate Relation instances.
        relation_data_processed = {}
        def process_recurse(part_id, template_part):
            """

            Returns
            -------
            relation_id : int
            relation : :class:`.Relation`
            """

            if part_id in relation_data_processed:
                return relation_data_processed[part_id]

            part_data = {
                'createdBy': request.user,
                'occursIn_id': data['occursIn']
            }
            for field in ['source', 'predicate', 'object']:

                node_type = getattr(template_part, '%s_node_type' % field)
                evidence_required = getattr(template_part, '%s_prompt_text' % field)

                if node_type == RelationTemplatePart.TYPE:
                    field_data = relation_data[part_id][field]
                    part_data['%s_object_id' % field] = int(field_data['appellation']['id'])
                    part_data['%s_content_type' % field] = ContentType.objects.get_for_model(Appellation)
                elif node_type == RelationTemplatePart.RELATION:
                    # -vv- Recusion happens here! -vv-
                    child_part = getattr(template_part, '%s_relationtemplate' % field)
                    part_data['%s_object_id' % field], part_data['%s_content_type' % field] = process_recurse(child_part.id, child_part)
                    relation_dependency_graph.add_edge(part_id, part_data['%s_object_id' % field])
                else:   # We will need to create an Appellation.
                    field_data = relation_data[part_id].get(field, None)
                    part_data['%s_object_id' % field] = _create_appellation(field_data, template_part, field, evidence_required).id
                    part_data['%s_content_type' % field] = ContentType.objects.get_for_model(Appellation)

            part_data['predicate_id'] = part_data['predicate_object_id']
            del part_data['predicate_object_id']
            del part_data['predicate_content_type']
            part_data['part_of'] = relation_set

            relation = Relation(**part_data)
            relation.save()
            relation_data_processed[part_id] = (relation.id, ContentType.objects.get_for_model(Relation))
            return (relation.id, ContentType.objects.get_for_model(Relation))


        for part_id, template_part in template_parts.iteritems():
            process_recurse(part_id, template_part)

        # The first element should be the root of the graph. This is where we
        #  need to "attach" the temporal relations.
        if len(template_parts) == 1:
            root = template_parts.keys()[0]
        else:
            root = nx.topological_sort(relation_dependency_graph)[0]

        for temporalType in ['start', 'end', 'occur']:
            temporalData = data.get(temporalType, None)
            if temporalData:

                # The predicate indicates the type of temporal dimension.
                predicate_uri = settings.TEMPORAL_PREDICATES.get(temporalType)
                if not predicate_uri:
                    continue
                predicate_concept = Concept.objects.get_or_create(uri=predicate_uri, defaults={'authority': 'Conceptpower'})[0]
                predicate_data = {
                    'occursIn_id': data['occursIn'],
                    'createdBy_id': request.user.id,
                    'interpretation': predicate_concept,
                    'asPredicate': True,
                }
                predicate_appellation = Appellation(**predicate_data)
                predicate_appellation.save()

                # The object need not have a URI (concept) interpretation; we
                #  use an ISO8601 date literal instead. This non-concept
                #  appellation is represented internally as a DateAppellation.
                object_data = {
                    'occursIn_id': data['occursIn'],
                    'createdBy_id': request.user.id,
                }
                for field in ['year', 'month', 'day']:
                    value = temporalData.get(field)
                    if not value:
                        continue
                    object_data[field] = value

                object_appellation = DateAppellation(**object_data)
                object_appellation.save()

                temporalRelation = Relation(**{
                    'source_content_type': ContentType.objects.get_for_model(Relation),
                    'source_object_id': relation_data_processed[root][0],
                    'part_of': relation_set,
                    'predicate': predicate_appellation,
                    'object_content_type': ContentType.objects.get_for_model(DateAppellation),
                    'object_object_id': object_appellation.id,
                    'occursIn_id': data['occursIn'],
                    'createdBy_id': request.user.id,
                })
                temporalRelation.save()

        response_data = {'relationset': relation_set.id}
    else:   # Not sure if we want to do anything for GET requests at this point.
        response_data = {}

    return JsonResponse(response_data)
