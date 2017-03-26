from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, Count
# from django.db.models.expressions import DateTime
from django.utils.safestring import SafeText

from annotations.models import Appellation, RelationSet, Relation

from collections import OrderedDict
from itertools import groupby, combinations, chain
import pytz
import re


def get_snippet_relation(relationset):
    """
    Get a text snippet for a :class:`annotations.models.RelationSet` instance.
    """

    appellation_type = ContentType.objects.get_for_model(Appellation)
    tokenizedContent = relationset.occursIn.tokenizedContent
    annotated_words = []

    # We'll use this to label highlighted tokens with their interpretations.
    annotation_map = {}

    fields = [
        'source_content_type_id',
        'object_content_type_id',
        'source_object_id',
        'object_object_id',
        'predicate__tokenIds',
        'predicate__interpretation__label',
        'predicate__interpretation_id',
    ]

    appellation_ids = set()

    # Pull out all Appellations that have a specific textual basis.
    for relation in relationset.constituents.values(*fields):
        for part in ['source', 'object']:
            if relation.get('%s_content_type_id' % part, None) == appellation_type.id:
                appellation_ids.add(relation['%s_object_id' % part])

        # Predicates too, since we're interested in evidence for the relation.
        if relation['predicate__tokenIds']:
            tokenIds = relation['predicate__tokenIds'].split(',')
            annotated_words.append(tokenIds)
            for t in tokenIds:
                annotation_map[t] = relation['predicate__interpretation__label']

    appellation_fields = [
        'tokenIds',
        'interpretation__label',
        'interpretation_id',
        'interpretation__merged_with_id',
        'interpretation__merged_with__label',
    ]
    for appellation in Appellation.objects.filter(pk__in=appellation_ids).values(*appellation_fields):

        tokenIds = appellation['tokenIds'].split(',')
        annotated_words.append(tokenIds)
        for t in tokenIds:
            if appellation['interpretation__merged_with_id']:
                annotation_map[t] = appellation['interpretation__merged_with__label']
            else:
                annotation_map[t] = appellation['interpretation__label']

    # Group sequences of tokens from appellations together if they are in close
    #  proximity.
    grouped_words = []
    for tokenSeq in sorted(annotated_words, key=lambda s: min([int(t) for t in s])):
        tokenSeqI = [int(t) for t in tokenSeq]
        match = False
        for i, tokensSeqGrouped in enumerate(grouped_words):
            tokensSeqGroupedI = [int(t) for t in tokensSeqGrouped]
            # If the current token sequence is contained within or overlaps with
            #  the token sequence group, then add it to the current group and
            #  exit.
            if (min(tokenSeqI) >= min(tokensSeqGroupedI) - 10 and max(tokenSeq) <= max(tokensSeqGroupedI) + 10) or \
               (min(tokenSeqI) - 10 <= min(tokensSeqGroupedI) <= max(tokenSeqI) + 10) or \
               (max(tokenSeqI) + 10 >= max(tokensSeqGroupedI) >= min(tokenSeqI) - 10):
               grouped_words[i] = tokensSeqGrouped + tokenSeq
               match = True
               break

        if not match:    # Sequence belongs to its own group (for now).
            grouped_words.append(tokenSeq)

    # Now build the snippet.
    combined_snippet = u""
    for tokenSeq in grouped_words:
        snippet = u""
        start_index = max(0, min([int(t) for t in tokenSeq])) - 5
        end_index = max([int(t) for t in tokenSeq]) + 5
        for i in range(start_index, end_index):
            match = re.search(r'<word id="'+str(i)+'">([^<]*)</word>', tokenizedContent, re.M|re.I)
            if not match:
                continue
            word = ""
            if str(i) in tokenSeq:
                # Tooltip shows the interpretation (Concept) for this
                #  Appellation.
                word = u"<strong data-toggle='tooltip' title='%s' class='text-warning text-snippet'>%s</strong>" % (annotation_map[str(i)], match.group(1))
            else:
                word = match.group(1)
            snippet = u'%s %s' % (snippet, word)
        combined_snippet += u' ...%s... ' % snippet.strip()
    return SafeText(combined_snippet)


def get_snippet(appellation):
    """
    Extract the text content surrounding (and including) an
    :class:`.Appellation` instance.

    Parameters
    ----------
    appellation : :class:`annotations.models.Appellation`

    Returns
    -------
    snippet : :class:`django.utils.safestring.SafeText`
        Includes emphasis tags surrounding the :class:`.Appellation`\'s
        tokens.
    """
    if not appellation['tokenIds']:
        return SafeText('No snippet is available for this appellation')

    tokenizedContent = appellation['occursIn__tokenizedContent']
    annotated_words = [i.strip() for i in appellation['tokenIds'].split(',')]
    middle_index = int(annotated_words[max(len(annotated_words)/2, 0)])
    start_index = max(middle_index - 10, 0)
    end_index = middle_index + 10
    snippet = ""
    for i in range(start_index, end_index):
        match = re.search(r'<word id="'+str(i)+'">([^<]*)</word>', tokenizedContent, re.M|re.I)
        if not match:
            continue

        word = ""

        if str(i) in annotated_words:
            word = u"<strong class='text-warning text-snippet'>%s</strong>" % match.group(1)
        else:
            word = match.group(1)
        snippet = u'%s %s' % (snippet, word)
    return SafeText(u'...%s...' % snippet.strip())


def get_appellation_summaries(appellations):
    """
    Generate appellation summary information for display in the text detail
    view.

    Parameters
    ----------
    appellations : :class:`django.db.models.query.QuerySet`

    Returns
    -------
    tuple
        (list, set)
    """
    appellations = appellations.order_by('interpretation_id')

    fields = [
        'interpretation_id',
        'interpretation__label',
        'interpretation__typed__label',
        'interpretation__merged_with_id',
        'interpretation__merged_with__label',
        'interpretation__merged_with__typed__label',
        'occursIn_id',
        'occursIn__tokenizedContent',
        'tokenIds',
        'createdBy_id',
        'createdBy__username',
        'created',
    ]

    appellations = appellations.values(*fields)
    appellations_data = []

    appellation_creators = set()
    groupkey = lambda a: a['interpretation__merged_with_id'] if a['interpretation__merged_with_id'] else a['interpretation_id']
    for concept_id, concept_appellations in groupby(appellations, groupkey):
        indiv_appellations = []
        unique_texts = set()
        for i, appellation in enumerate(concept_appellations):
            # We have to do this in here, because ``appellation`` is an
            #  itertools._grouper iterable.
            if i == 0:
                if appellation['interpretation__merged_with__typed__label']:
                    type_label = appellation['interpretation__merged_with__typed__label']
                elif appellation['interpretation__typed__label']:
                    type_label = appellation['interpretation__typed__label']
                else:
                    type_label = u''
                if appellation['interpretation__merged_with__label']:
                    concept_label = appellation['interpretation__merged_with__label']
                else:
                    concept_label = appellation['interpretation__label']

            indiv_appellations.append({
                "text_snippet": get_snippet(appellation),
                "annotator_id": appellation['createdBy_id'],
                "annotator_username": appellation['createdBy__username'],
                "created": appellation['created'],
            })
            appellation_creators.add(appellation['createdBy_id'])
            unique_texts.add(appellation['occursIn_id'])

        num_texts = len(unique_texts) - 1
        appellations_data.append({
            "interpretation_id": concept_id,
            "interpretation_label": concept_label,
            "interpretation_type": type_label,
            "appellations": indiv_appellations,
            "num_texts": num_texts,
        })

    appellations_data = sorted(appellations_data,
                               key=lambda a: a['interpretation_label'])

    return appellations_data, appellation_creators


def get_relations_summaries(relationset_qs):
    """
    Organize RelationSets for this text so that we can display them in
    conjunction with edges in the graph. In other words, grouped by
    the "source" and "target" of the simplified graphical representation.

    Parameters
    ----------
    relationset_qs : :class:`django.db.models.query.QuerySet`

    Returns
    -------
    list
    """

    app_ct = ContentType.objects.get_for_model(Appellation)
    relationsets_by_interpretation = []
    relationsets = []

    fields = [
        'source_content_type_id',
        'object_content_type_id',
        'source_object_id',
        'object_object_id',
        'predicate__tokenIds',
        'predicate__interpretation__label',
        'predicate__interpretation_id',
    ]

    # Pull out "focal" concepts from the RelationSet. Usually there will
    #  be only two, but there could be more.
    for relationset in relationset_qs:
        appellation_ids = set()
        for rel in relationset.constituents.all().values(*fields):
            for part in ['source', 'object']:
                if rel.get('%s_content_type_id' % part, None) == app_ct.id:
                    appellation_ids.add(rel['%s_object_id' % part])

        interps = []    # Focal concepts go here.
        appellations = Appellation.objects.filter(pk__in=appellation_ids, asPredicate=False)
        appellation_fields = [
            'interpretation_id',
            'interpretation__label',
            'interpretation__typed__label',
            'interpretation__merged_with_id',
            'interpretation__merged_with__label',
            'interpretation__merged_with__typed__label',
        ]
        for appellation in appellations.values(*appellation_fields):
            if appellation['interpretation__merged_with_id']:
                interps.append((appellation['interpretation__merged_with_id'], appellation['interpretation__merged_with__label']))
            else:
                interps.append((appellation['interpretation_id'], appellation['interpretation__label']))

        # Usually there will be only two Concepts here, but for more complex
        #  relations there could be more.
        for u, v in combinations(interps, 2):
            u, v = tuple(sorted([u, v], key=lambda a: a[0]))
            # This is kind of hacky, but it lets us access the IDs and
            #  labels more readily below.
            rset = ((u[0], u[1], v[0], v[1]), relationset)
            relationsets_by_interpretation.append(rset)

    # Here we sort and group by concept-pairs (u and v, above).
    skey = lambda r: r[0]
    rsets = groupby(sorted(relationsets_by_interpretation, key=skey),
                    key=skey)

    # Each group will be shown as an accordion panel in the view.
    for (u_id, u_label, v_id, v_label), i_relationsets in rsets:
        relationsets.append({
            "source_interpretation_id": u_id,
            "source_interpretation_label": u_label,
            "target_interpretation_id": v_id,
            "target_interpretation_label": v_label,
            "relationsets": [{
                "text_snippet": get_snippet_relation(relationset),
                "annotator": relationset.createdBy,
                "created": relationset.created,
            } for _, relationset in i_relationsets]
        })
    return relationsets


def user_recent_texts(user):
    """
    Return a list of :class:`.Text`\s recently annotated by a
    :class:`.VogonUser`\.

    TODO: Do we need this anymore?

    Parameters
    ----------
    user : :class:`.VogonUser`

    Returns
    -------
    list
    """
    fields = ['occursIn_id', 'occursIn__title', 'created']
    by_appellations = user.appellation_set.all().order_by('-created')\
                                          .values_list(*fields)
    by_relations = user.relation_set.all().order_by('-created')\
                                    .values_list(*fields)

    results_sorted = sorted(chain([tuple(t) for t in by_relations],
                                  [tuple(t) for t in by_appellations]),
                            key=lambda t: t[2])[::-1]

    return list(set([(t[0], t[1]) for t in results_sorted]))


# def get_recent_annotations(last=20, user=None):
#     """
#     Generate aggregate activity feed for all annotations.
#
#     TODO: move this into a util module.
#
#     Parameters
#     ----------
#     last : int
#         Number of items to return (default: 20).
#     user : :class:`.VogonUser`
#
#     Returns
#     -------
#     dict
#     """
#     recent_appellations = Appellation.objects.all()
#     recent_relations = Relation.objects.all()
#
#     if user:
#         recent_appellations = recent_appellations.filter(createdBy_id=user.id)
#         recent_relations = recent_relations.filter(createdBy_id=user.id)
#
#     recent_appellations = recent_appellations.annotate(hour=DateTime("created", "hour", pytz.timezone("UTC")))\
#         .values("hour", "createdBy__username", "createdBy__id")\
#         .annotate(appelation_count=Count('id'))\
#         .order_by("-hour")
#     recent_relations = recent_relations.annotate(hour=DateTime("created", "hour", pytz.timezone("UTC")))\
#         .values("hour", "createdBy__username", "createdBy__id")\
#         .annotate(relation_count=Count('id'))\
#         .order_by("-hour")
#
#     combined_data = OrderedDict()
#     for event in recent_appellations:
#         key = (event['hour'], event['createdBy__username'], event['createdBy__id'])
#         if key not in combined_data:
#             combined_data[key] = {'appelation_count': event['appelation_count'], 'relation_count': 0}
#         combined_data[key]['appelation_count'] += event['appelation_count']
#     for event in recent_relations:
#         key = (event['hour'], event['createdBy__username'], event['createdBy__id'])
#         if key not in combined_data:
#             combined_data[key] = {'appelation_count': 0, 'relation_count': event['relation_count']}
#         combined_data[key]['relation_count'] += event['relation_count']
#     return dict(sorted(combined_data.items(), key=lambda k: k[0][0])[::-1][:last])


def get_recent_annotations_for_graph(annotation_by_user, start_date):
    result = dict()
    weeks_last_date_map = dict()
    d7 = datetime.timedelta( days = 7)
    current_week = datetime.datetime.now() + d7

    # Find out the weeks and their last date in the past 90 days.
    while start_date <= current_week:
        result[(Week(start_date.isocalendar()[0], start_date.isocalendar()[1]).saturday()).strftime('%m-%d-%y')] = 0
        start_date += d7
    time_format = '%Y-%m-%d'

    # Count annotations for each week.
    for count_per_day in annotation_by_user:
        if(isinstance(count_per_day['date'], unicode)):
            date = datetime.datetime.strptime(count_per_day['date'], time_format)
        else:
            date = count_per_day['date']
        result[(Week(date.isocalendar()[0], date.isocalendar()[1]).saturday()).strftime('%m-%d-%y')] += count_per_day['count']
    annotation_per_week = list()

    # Sort the date and format the data in the format required by d3.js.
    keys = (result.keys())
    keys.sort()
    for key in keys:
        new_format = dict()
        new_format["date"] = key
        new_format["count"] = result[key]
        annotation_per_week.append(new_format)
    annotation_per_week = str(annotation_per_week).replace("'", "\"")
    return annotation_per_week


def filter_relationset(qs, params):
    """
    """
    parameter_map = [
        ('text', 'occursIn_id__in'),
        ('project', 'occursIn__partOf__in'),
        ('text_published_from', 'occursIn__created__gte'),
        ('text_published_through', 'occursIn__created__lte'),
        ('user', 'createdBy__in'),
        ('created_from', 'created__gte'),
        ('created_through', 'created__lte'),
    ]

    parameters = {}
    for param, field in parameter_map:
        if param in ['text', 'project', 'user']:
            value = params.getlist(param, [])
        else:
            value = params.get(param, None)
        if value and value[0]:
            parameters[field] = value

    qs = qs.filter(**parameters)

    node_types = params.getlist('node_types')
    exclusive = params.get('exclusive', 'off')

    # We need this ContentType to filter on Relations, since .source and .object
    #  are Generic relations.
    app_ct = ContentType.objects.get_for_model(Appellation)

    # Limit to RelationSets whose Appellations refer to Concepts of a
    #  specific Type.
    if node_types:
        appellations = Appellation.objects.filter(**parameters)\
                                          .filter(interpretation__typed__in=node_types)\
                                          .values_list('id', flat=True)
        q_source = Q(constituents__source_content_type=app_ct)\
                   & Q(constituents__source_object_id__in=appellations)
        q_object = Q(constituents__object_content_type=app_ct)\
                   & Q(constituents__object_object_id__in=appellations)
        if exclusive == 'on':
            q = q_source & q_object
        else:
            q = q_source | q_object
        qs = qs.filter(q)

    # Limit to RelationSets whose Appellations refer to specific Concepts.
    nodes = params.getlist('nodes')

    if nodes:
        appellations = Appellation.objects.filter(**parameters)\
                                          .filter(interpretation__in=nodes)\
                                          .values_list('id', flat=True)
        q = (Q(constituents__source_content_type=app_ct) & Q(constituents__source_object_id__in=appellations) |
             Q(constituents__object_content_type=app_ct) & Q(constituents__object_object_id__in=appellations))
        qs = qs.filter(q)

    # We have filtered based on related fields, which means that if we were to
    #  call values() or values_list() on those related fields we would be
    #  limited not only to the selected RelationSets but also to the specific
    #  passing values. Re-filtering based on ID ensures that we can get all of
    #  the relevant related fields for the RelationSets in our QuerySet.
    return RelationSet.objects.filter(id__in=qs.values_list('id', flat=True))
