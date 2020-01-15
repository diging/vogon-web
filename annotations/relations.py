"""
Business logic for building and using :class:`.RelationTemplate`\s.
"""

from django.db import transaction
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

from annotations.models import *
from concepts.models import Concept

import networkx as nx
from string import Formatter


PRED_MAP = {    # Used in expression and terminal node templates.
    's': 'source_content_object',
    'p': 'predicate',
    'o': 'object_content_object'
}


class InvalidTemplate(RuntimeError):
    pass


class InvalidData(RuntimeError):
    pass


datum_as_key = lambda datum: (datum['part_id'], datum['part_field'])


def get_fields(template):
    """
    Retrieve the set of fields that are required to generate a new
    :class:`.RelationSet` from a :class:`.RelationTemplate`\. These fields can
    be used to generate :class:`.Appellation`\s that will be used in the
    eventual :class:`.RelationSet`\.

    Each field should be specified using the following keys:

    ================    ========================================================
    type                A value from :prop:`.RelationTemplatePart.NODE_CHOICES`
    part_id             The pk-id of the template part to which this field
                        belongs (int).
    part_field          The name of the field (source, predicate, object).
    concept_id          If a TYPE field, this is the pk-id of the
                        :class:`concepts.models.Type` to which the
                        interpretation should belong. Otherwise, the pk-id of
                        the specified  :class:`concepts.models.Concept` to be
                        used as the interpretation (int).
    concept_label       The display label for the selected concept (str).
    label               The display label for the field (str).
    evidence_required   Whether or not a text selection is required for the
                        appellation (bool).
    description         A freeform description (to be displayed along with
                        ``label``) of the field (str).
    ================    ========================================================


    Parameters
    ----------
    template : :class:`annotations.models.RelationTemplate`

    Returns
    -------
    list
        Each item is a dict specifying the nature of the field.
    """

    fields = []
    for tpart in template.template_parts.all():
        for field in ['source', 'predicate', 'object']:
            evidenceRequired = getattr(tpart, '%s_prompt_text' % field)
            nodeType = getattr(tpart, '%s_node_type' % field)
            # The user needs to provide specific concepts for TYPE fields.
            if nodeType == RelationTemplatePart.TYPE:
                part_type = getattr(tpart, '%s_type' % field)
                part_label = getattr(tpart, '%s_label' % field)
                part_description = getattr(tpart, '%s_description' % field)
                concept_id = getattr(part_type, 'id', None)
                concept_label = getattr(part_type, 'label', None)
                fields.append({
                    'type': 'TP',
                    'part_id': tpart.id,
                    'part_field': field,
                    'concept_id': concept_id,
                    'label': part_label,
                    'concept_label': concept_label,
                    'evidence_required': evidenceRequired,
                    'description': part_description,
                })
            elif nodeType == RelationTemplatePart.DATE:
                part_type = getattr(tpart, '%s_type' % field)
                part_label = getattr(tpart, '%s_label' % field)
                part_description = getattr(tpart, '%s_description' % field)
                concept_id = getattr(part_type, 'id', None)
                concept_label = getattr(part_type, 'label', None)
                fields.append({
                    'type': 'DT',
                    'part_id': tpart.id,
                    'part_field': field,
                    'concept_id': concept_id,
                    'label': part_label,
                    'concept_label': concept_label,
                    'evidence_required': evidenceRequired,
                    'description': part_description,
                })

            # Even if there is an explicit concept, we may require textual
            #  evidence from the user.
            elif evidenceRequired and nodeType == RelationTemplatePart.CONCEPT:
                part_concept = getattr(tpart, '%s_concept' % field)
                concept_id = getattr(part_concept, 'id', None)
                concept_label = getattr(part_concept, 'label', None)
                part_label = getattr(tpart, '%s_label' % field)
                part_description = getattr(tpart, '%s_description' % field)
                fields.append({
                    'type': 'CO',
                    'part_id': tpart.id,
                    'part_field': field,
                    'concept_id': concept_id,
                    'label': part_label,
                    'concept_label': concept_label,
                    'evidence_required': evidenceRequired,
                    'description': part_description,
                })
    return fields


def build_dependency_graph_from_template(template):
    dependencies = nx.DiGraph()
    for template_part in template.template_parts.all():
        for pred in ['source', 'object']:
            node_type = getattr(template_part, '%s_node_type' % pred)
            if node_type == RelationTemplatePart.RELATION:
                dependencies.add_edge(template_part.internal_id, getattr(template_part, '%s_relationtemplate' % pred).internal_id)
    return dependencies


def build_dependency_graph(template_data, part_data, **kwargs):
    dependencies = nx.DiGraph()
    for part_datum in part_data:
        part_internal_id = int(part_datum['internal_id'])
        for pred in ['source', 'object']:
            target_id = int(part_datum['%s_relationtemplate_internal_id' % pred])
            if target_id > -1:
                dependencies.add_edge(part_internal_id, target_id)
    return dependencies


def validate_terminal_nodes(template_data, part_data, **kwargs):
    """
    The terminal nodes expression should be a comma-separate list of relation
    template part internal IDs and their relation part flags. For example:
    ``0s,1o`` refers to the subject of the first part and object of the second
    part.
    """
    N_parts = len(part_data)
    terminal_nodes = template_data.get('terminal_nodes', '')
    try:
        for part_id, pred_flag in map(tuple, terminal_nodes.split(',')):
            if not int(part_id) <= N_parts:
                raise InvalidTemplate("Part ID in terminal nodes is invalid.")
            if not pred_flag in ['s', 'p', 'o']:
                raise InvalidTemplate("Node ID in terminal nodes is invalid.")
    except Exception as E:
        raise InvalidTemplate("Invalid pattern for terminal nodes")


def validate_expression(template_data, part_data, **kwargs):
    N_parts = len(part_data)

    try:
        keys = list(zip(*list(Formatter().parse(template_data.get('expression')))))[1]
        for part_id, pred_flag in map(tuple, keys):
            if not int(part_id) <= N_parts:
                raise InvalidTemplate("Part ID in expression is invalid.")
            if not pred_flag in ['s', 'p', 'o']:
                raise InvalidTemplate("Node ID in expression is invalid.")
    except ValueError as E:
        # Raised if there are not precisely two characters in each key.
        raise InvalidTemplate("Each key in the expression must be precisely"
                              " two characters long")
    except Exception as E:
        raise InvalidTemplate("Invalid expression pattern")


def validate_template_data(template_data, part_data, **kwargs):
    validate_terminal_nodes(template_data, part_data)
    validate_expression(template_data, part_data)


    dependencies = build_dependency_graph(template_data, part_data)
    if not dependencies.number_of_selfloops() == 0:
        raise InvalidTemplate('Relation structure contains self-loops')

    if not nx.algorithms.is_directed_acyclic_graph(dependencies):
        raise InvalidTemplate('Relation structure is cyclic or disconnected')


def parse_template_part_data(part_data, **kwargs):
    node_fields = {
        RelationTemplatePart.TYPE: ('type', 'description'),
        RelationTemplatePart.DATE: ('type', 'description'),
        RelationTemplatePart.CONCEPT: ('concept', 'description'),
        RelationTemplatePart.RELATION: ('relationtemplate_internal_id',)
    }
    data = {'internal_id': part_data['internal_id']}

    for pred in ['source', 'predicate', 'object']:
        data['%s_node_type' % pred] = part_data['%s_node_type' % pred]
        data['%s_prompt_text' % pred] = part_data['%s_prompt_text' % pred]
        data['%s_label' % pred] = part_data['%s_label' % pred]
        data.update({
            '%s_%s' % (pred, field): part_data['%s_%s' % (pred, field)]
            for field in node_fields.get(part_data['%s_node_type' % pred], [])
        })
    return data


def create_template(template_data, part_data):
    """
    Create a new :class:`.RelationTemplate` and constituent
    :class:`.RelationTemplatePart`\s from form/formset data.

    Parameters
    ----------
    template_data : dict
        Cleaned data from a :class:`annotations.forms.RelationTemplateForm`\.
    part_data : list
        Each element should be a ``dict`` with data from a
        :class:`annotations.forms.RelationTemplatePartForm`\.

    Returns
    -------
    :class:`annotations.models.RelationTemplate`
    """
    validate_template_data(template_data, part_data)

    # Each RelationTemplatePart is a "triple", the subject or object of which
    #  might be another RelationTemplatePart.
    dependencies = dict(build_dependency_graph(template_data, part_data).edges())
    part_ids = {}    # Internal IDs to PK ids for RelationTemplatePart.

    creation_data = list(map(parse_template_part_data, part_data))

    with transaction.atomic():
        template = RelationTemplate.objects.create(**template_data)
        for datum in creation_data:
            datum['part_of_id'] = template.id

        parts = {
            datum['internal_id']: RelationTemplatePart.objects.create(**datum)
            for datum in creation_data
        }
        for part in list(parts.values()):
            for pred in ['source', 'object']:
                internal = getattr(part, '%s_relationtemplate_internal_id' % pred)
                if internal > -1:
                    setattr(part, '%s_relationtemplate' % pred, parts[internal])
                    part.save()
    return template


def create_appellation(field_data, field, cache={}, project_id=None, creator=None, text=None):
    """
    Some fields may have data for appellations that have not yet been
    created. So we do that here.
    """
    if cache:
        key = datum_as_key(field_data)
        if key in cache:
            return cache[key]

    appellation_data = {
        'occursIn': text,
        'createdBy': creator,
        'project_id': project_id
    }

    position_data = field_data.pop('position', None)

    if position_data:
        position = DocumentPosition.objects.create(**position_data)
        appellation_data.update({
            'position': position,
        })

    appellation_data.update({
        'tokenIds': field_data.get('data', {}).get('tokenIds', ''),
        'stringRep': field_data.get('data', {}).get('stringRep', ''),
    })


    node_type = field.get('type')
    if node_type == RelationTemplatePart.CONCEPT:
        # The interpretation is already provided.
        appellation_data['interpretation_id'] = field.get('concept_id')
    elif node_type == RelationTemplatePart.TOBE:
        appellation_data['interpretation'] = Concept.objects.get_or_create(uri=settings.PREDICATES.get('be'))[0]
    elif node_type == RelationTemplatePart.HAS:
        appellation_data['interpretation'] = Concept.objects.get_or_create(uri=settings.PREDICATES.get('have'))[0]    # "http://www.digitalhps.org/concepts/CON83f5110b-5034-4c95-82f8-8f80ff55a1b9"

    if field['part_field'] == 'predicate':
        appellation_data['asPredicate'] = True

    appellation = Appellation.objects.create(**appellation_data)

    if cache:
        cache[datum_as_key(field_data)] = appellation
    return appellation


def expression_partial(obj):
    if type(obj) is Appellation:
        return obj.interpretation.label
    elif type(obj) is DateAppellation:
        return obj.dateRepresentation
    return obj.__unicode__


def generate_expression(template, relations):
    # Generate a human-readable phrase that expresses the relation.
    expression_keys = [k[1].replace('_', '') for k in Formatter().parse(template.expression)
                       if k[1] is not None]
    expression_data = {}
    for key in expression_keys:
        try:
            relation = relations[int(key[0])]
            attr_name = PRED_MAP.get(key[1])
            value = expression_partial(getattr(relation, attr_name))
        except ValueError:
            value = '[missing]'
        except KeyError:
            value = '[missing]'
        if not attr_name:
            continue

        expression_data[key] = value
    return template.expression.replace('_', '').format(**expression_data)


def get_terminal_nodes(template, relations):
    nodes = []
    if not template.terminal_nodes:
        return nodes

    for key in template.terminal_nodes.split(','):
        try:
            obj = getattr(relations[int(key[0])], PRED_MAP.get(key[1]))
        except KeyError:
            continue
        if hasattr(obj, 'interpretation') and obj.interpretation:
            nodes.append(obj.interpretation)
    return nodes


def handle_temporal_data(template, data, creator, text, relationset, relations, project_id=None):
    depgraph = build_dependency_graph_from_template(template)
    if depgraph.size() == 0:
        root = template.template_parts.first().internal_id
    else:
        root = list(nx.topological_sort(depgraph))[0]
    top_relation = relations[root]    # To which we attach temporal relations.

    for relation_type in ['start', 'end', 'occur']:
        relation_data = data.get(relation_type)
        if not relation_data:
            continue

        # The predicate indicates the type of temporal dimension.
        predicate_uri = settings.TEMPORAL_PREDICATES.get(relation_type)
        if not predicate_uri:
            continue
        predicate_concept, _ = Concept.objects.get_or_create(uri=predicate_uri,
                                                             defaults={'authority': 'Conceptpower'})
        predicate_data = {
            'occursIn': text,
            'createdBy': creator,
            'interpretation': predicate_concept,
            'asPredicate': True,
        }
        if project_id:
            predicate_data.update({'project_id': project_id})
        predicate_appellation = Appellation.objects.create(**predicate_data)

        # The object/target of the relation is a DateAppellation, which we may
        #  or may not have to create (depending on the annotator/version).
        temporal_id = relation_data.get('id')
        if temporal_id:
            object_appellation = DateAppellation.objects.get(pk=temporal_id)
        else:
            # The object need not have a URI (concept) interpretation; we
            #  use an ISO8601 date literal instead. This non-concept
            #  appellation is represented internally as a DateAppellation.
            object_data = {
                'occursIn': text,
                'createdBy': creator,
            }
            if project_id:
                object_data.update({'project_id': project_id})
            for field in ['year', 'month', 'day']:
                value = relation_data.get(field)
                if not value:
                    continue
                object_data[field] = value
            object_appellation = DateAppellation.objects.create(**object_data)

        temporalRelation = Relation(**{
            'source_content_object': top_relation,
            'part_of': relationset,
            'predicate': predicate_appellation,
            'object_content_object': object_appellation,
            'occursIn': text,
            'createdBy': creator,
        })
        temporalRelation.save()


def create_relationset(template, raw_data, creator, text, project_id=None):
    """
    Create a new :class:`annotations.models.RelationSet` instance from a
    :class:`annotations.models.RelationTemplate` and user data.
    """

    _as_key = lambda datum: (datum['part_id'], datum['part_field'])
    required = {_as_key(datum): datum for datum in get_fields(template)}
    provided = {_as_key(datum): datum for datum in raw_data['fields']}
    template_parts = template.template_parts.all()

    missing = set(required.keys()) - set(provided.keys())
    if len(missing) > 0:
        raise InvalidData('Missing fields: %s' % '; '.join(list(remaining)))

    def create_relation(template_part, data, relationset, cache={}, appellation_cache={}, project_id=None):
        if cache != None:
            key = template_part.id 
            if key in cache:
                return cache[key]

        field_handlers = {
            RelationTemplatePart.TYPE: lambda datum: Appellation.objects.get(pk=datum['appellation']['id']),
            RelationTemplatePart.DATE: lambda datum: DateAppellation.objects.get(pk=datum['appellation']['id']),
            '__other__': lambda datum: create_appellation(datum, required[_as_key(datum)], cache=appellation_cache, project_id=project_id, creator=creator, text=text)
        }

        relation_data = {
            'part_of': relationset,
            'createdBy': creator,
            'occursIn': text,
        }

        for pred in ['source', 'predicate', 'object']:    # Collect field data
            node_type = getattr(template_part, '%s_node_type' % pred)
            method = field_handlers.get(node_type, field_handlers['__other__'])
            datum = provided.get((template_part.id, pred))

            dkey = 'predicate' if pred == 'predicate' else '%s_content_object' % pred

            if datum:
                relation_data[dkey] = method(datum)
            elif node_type == RelationTemplatePart.RELATION:
                relation_data[dkey] = create_relation(getattr(template_part, '%s_relationtemplate' % pred), data, relationset, cache=cache, appellation_cache=appellation_cache, project_id=project_id)
            else:
                payload = {
                    'type': node_type,
                    'concept_id': getattr(getattr(template_part, '%s_concept' % pred), 'id', None),
                    'part_field': pred
                }
                relation_data[dkey] = create_appellation({}, payload, project_id=project_id, creator=creator, text=text)

        relation = Relation.objects.create(**relation_data)

        if cache != None:
            cache[template_part.id] = relation
        return relation

    appellation_cache = {}
    relation_cache = {}
    relations = {}
    with transaction.atomic():
        relationset = RelationSet.objects.create(**{
            'createdBy': creator,
            'occursIn': text,
            'template': template,
            'project_id': project_id
        })
        for template_part in template_parts:
            relation = create_relation(template_part, provided, relationset, cache=relation_cache, appellation_cache=appellation_cache, project_id=project_id)
            relations[template_part.internal_id] = relation

        relationset.expression = generate_expression(template, relations)
        relationset.terminal_nodes.add(*get_terminal_nodes(template, relations))

        # Updates the RelationSet in place.
        handle_temporal_data(template, raw_data, creator, text, relationset,
                             relations, project_id=project_id)
        relationset.save()
    return relationset
