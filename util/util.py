def unescape(s):
    return s.replace('&amp;', '&')\
        .replace('&lt;', '<')\
        .replace('&gt;', '>')\
        .replace("&#39;", "'")\
        .replace('&quot;', '"')


def escape(s):
    """
    < is converted to &lt;
    > is converted to &gt;
    ' (single quote) is converted to &#39;
    " (double quote) is converted to &quot;
    & is converted to &amp;
    """
    return s.replace('&', '&amp;')\
        .replace('<', '&lt;')\
        .replace('>', '&gt;')\
        .replace("'", "&#39;")\
        .replace('"', '&quot;')


def correctPosition(position):
    text = position.occursIn
    manager = text.repository.manager(user)
    try:
        content_data = manager.content(id=int(text.repository_source_id))
        raw_content = requests.get(content_data['location']).content
    except IOError:
        print 'nope', text
        return
    start, end = map(int, position.position_value.split(','))
    escaped = escape(raw_content)
    start_o = len(unescape(escaped[:start]))
    end_o = len(unescape(escaped[:end]))
    # position.position_value = '%i,%i' % (start_o, end_o)
    # position.save()
    print start, end, ':: --> ::', start_o, end_o
    print escaped[start:end], unescape(escaped)[start_o:end_o]


from annotations.tasks import tokenize
def correctTaggedPosition(position):
    text = position.occursIn
    manager = text.repository.manager(user)
    try:
        content_data = manager.content(id=int(text.repository_source_id))
        raw_content = requests.get(content_data['location']).content
    except IOError:
        print 'nope', text
        return
    token_ids = map(int, position.position_value.split(','))
    start_id, end_id = min(token_ids), max(token_ids)
    tokenized = tokenize(raw_content.decode('utf-8'))
    start_ptn = '<word id="%i">' % start_id
    start_idx = tokenized.index(start_ptn) + len(start_ptn)
    end_ptn = '<word id="%i">' % end_id
    try:
        tok = re.search('<word id="%i">([^\<]+)</word>' % end_id, tokenized, flags=re.U).group(1)
    except AttributeError:
        print start_id, end_id, text.id
        raise
    end_idx = tokenized.index(end_ptn) + len(end_ptn) + len(tok)
    start_o = len(detokenize(tokenized[:start_idx]))
    end_o = len(detokenize(tokenized[:end_idx]))
    position.position_value = '%i,%i' % (start_o, end_o)
    position.position_type = 'CO'
    position.save()
    print start_idx, end_idx, ':: --> ::', start_o, end_o
    print tokenized[start_idx:end_idx], detokenize(tokenized)[start_o:end_o]


import re, codecs
tag_pattern = re.compile(r'((<word id=\"[0-9]+\">)|(</word>))', flags=re.U)
def detokenize(s):
    return re.sub(tag_pattern, '', s)


base_path = '/tmp/vogon-export'


def proc_text(text):
    """
    Extract content and serialize exportable data for Amphora.
    """
    fname = '%i__content.txt' % text.id
    fpath = os.path.join(base_path, fname)
    with codecs.open(fpath, 'w', encoding='utf-8') as f:
        f.write(detokenize(text.tokenizedContent))
    return {
        'name': text.title,
        'uri': text.uri,
        'file': fname,
        'original': text.originalResource
    }


import mimetypes
from cookies import operations
from django.db import transaction
def to_resource(datum):
    uri = datum.get('uri')
    if 'jstor' in uri:
        collection = jhb
    elif 'handle' in uri:
        collection = embryo
    with transaction.atomic():
        container = ResourceContainer.objects.create(created_by=user, part_of=collection)
        master = Resource.objects.create(
            name=datum['name'],
            uri=datum['uri'],
            created_by=user,
            container=container
        )
        container.primary = master
        container.save()
        original_location = datum.get('original')
        if original_location:
            external = Resource.objects.create(
                container=container,
                name=datum['name'],
                content_resource=True,
                location=original_location,
                is_external=True,
                created_by=user,
            )
            ContentRelation.objects.create(
                for_resource=master,
                container=container,
                content_resource=external,
                created_by=user,
            )
        base_path = '/home/amphora/vogon-export'
        fname = datum.get('file')
        fpath = os.path.join(base_path, fname)
        content = Resource.objects.create(**{
            'content_type': mimetypes.guess_type(fpath)[0],
            'content_resource': True,
            'name': fname,
            'created_by': user,
            'container': container,
        })
        operations.add_creation_metadata(content, user)
        with open(fpath, 'r') as f:
            uploaded_file = File(f)
            # The file upload handler needs the Resource to have an ID first,
            #  so we add the file after creation.
            content.file = uploaded_file
            content.save()
        content_relation = ContentRelation.objects.create(**{
            'for_resource': master,
            'content_resource': content,
            'content_type': content.content_type,
            'container': container,
        })
    return master




def create_from_file(path, collection, user, resource_data, creation_message):
    name = os.path.split(path)[-1]
    if collection.resourcecontainer_set.filter(primary__name=name).count() > 0:
        return
    container = ResourceContainer.objects.create(created_by=user, part_of=collection)
    content = Resource.objects.create(**{
        'content_type': mimetypes.guess_type(path)[0],
        'content_resource': True,
        'name': name,
        'created_by': user,
        'container': container,
    })
    operations.add_creation_metadata(content, user)
    with open(path, 'r') as f:
        uploaded_file = File(f)
        # The file upload handler needs the Resource to have an ID first,
        #  so we add the file after creation.
        content.file = uploaded_file
        content.save()
    resource_data['created_by'] = user
    resource_data['container'] = content.container
    resource = Resource.objects.create(**resource_data)
    content.container.primary = resource
    content.container.save()
    operations.add_creation_metadata(resource, user)
    Relation.objects.create(**{
        'source': resource,
        'predicate': __provenance__,
        'target': Value.objects.create(**{
            '_value': jsonpickle.encode(creation_message),
            'container': resource.container,
        }),
        'container': resource.container,
    })
    content_relation = ContentRelation.objects.create(**{
        'for_resource': resource,
        'content_resource': content,
        'content_type': content.content_type,
        'container': content.container,
    })
    resource.container = content.container
    resource.save()
    return resource.container




from annotations.tasks import tokenize
from django.db import transaction
def correctTaggedPosition(position):
    with transaction.atomic():
        text = position.occursIn
        try:
            token_ids = map(int, position.position_value.split(','))
        except ValueError:
            token_ids = None
        if token_ids:
            start_id, end_id = min(token_ids), max(token_ids)
            tokenized = text.tokenizedContent
            start_ptn = '<word id="%i">' % start_id
            start_idx = tokenized.index(start_ptn) + len(start_ptn)
            end_ptn = '<word id="%i">' % end_id
            try:
                tok = re.search('<word id="%i">([^\<]+)</word>' % end_id, tokenized, flags=re.U).group(1)
            except AttributeError:
                print start_id, end_id, text.id
                raise
            end_idx = tokenized.index(end_ptn) + len(end_ptn) + len(tok)
            start_o = len(detokenize(tokenized[:start_idx]))
            end_o = len(detokenize(tokenized[:end_idx]))
            position.position_value = '%i,%i' % (start_o, end_o)
            print start_idx, end_idx, ':: --> ::', start_o, end_o
            print tokenized[start_idx:end_idx], '-->', detokenize(tokenized)[start_o:end_o]
        else:
            position.position_value = ''
            print '-- Baseless --'
        position.position_type = 'CO'
        position.save()


{u'fields': {u'internal_id': 1,
             u'object_concept': None,
             u'object_description': u'The other of the two collaborators',
             u'object_label': u'Collaborator',
             u'object_node_type': u'TP',
             u'object_prompt_text': True,
             u'object_relationtemplate': None,
             u'object_relationtemplate_internal_id': -1,
             u'object_type': 2,
             u'part_of': 1,
             u'predicate_concept': None,
             u'predicate_description': None,
             u'predicate_label': u'',
             u'predicate_node_type': u'IS',
             u'predicate_prompt_text': True,
             u'predicate_type': None,
             u'source_concept': 8153,
             u'source_description': u'Please select the word or phrase that substantiates the fact or nature of the collaboration, excluding direct references to the actors themselves. For example, if the text says, "Bradshaw collaborated with Mobbs," then select the phrase, "collaborated with".',
             u'source_label': u'Evidence for the collaboration',
             u'source_node_type': u'CO',
             u'source_prompt_text': True,
             u'source_relationtemplate': None,
             u'source_relationtemplate_internal_id': -1,
             u'source_type': None},
 u'model': u'annotations.relationtemplatepart',
 u'pk': 1}

new_rtparts = {}
with transaction.atomic():
    for obj in rtpart_data:
        datum = obj['fields']
        object_concept = datum.get('object_concept')
        if object_concept:
            object_concept = concept_id_map[int(object_concept)]
        source_concept = datum.get('source_concept')
        if source_concept:
            source_concept = concept_id_map[int(source_concept)]
        predicate_concept = datum.get('predicate_concept')
        if predicate_concept:
            predicate_concept = concept_id_map[int(predicate_concept)]
        newpart = RelationTemplatePart.objects.create(
            internal_id=datum['internal_id'],
            object_description=datum['object_description'],
            source_description=datum['source_description'],
            predicate_description=datum['predicate_description'],
            source_concept_id=source_concept,
            object_concept_id=object_concept,
            predicate_concept_id=predicate_concept,
            object_label=datum['object_label'],
            source_label=datum['source_label'],
            predicate_label=datum['predicate_label'],
            object_node_type=datum['object_node_type'],
            source_node_type=datum['source_node_type'],
            predicate_node_type=datum['predicate_node_type'],
            object_prompt_text=datum['object_prompt_text'],
            source_prompt_text=datum['source_prompt_text'],
            predicate_prompt_text=datum['predicate_prompt_text'],
            object_relationtemplate_internal_id=datum['object_relationtemplate_internal_id'],
            source_relationtemplate_internal_id=datum['source_relationtemplate_internal_id'],
            object_type=type_lookup.get(datum['object_type']),
            source_type=type_lookup.get(datum['source_type']),
            predicate_type=type_lookup.get(datum['predicate_type']),
            part_of_id=rtemplate_map.get(datum['part_of'])
        )
        new_rtparts[obj['pk']] = newpart



for rc in chain(jhb.resourcecontainer_set.all(), embryo.resourcecontainer_set.all()):
    uri = rc.primary.uri
    rid = rc.primary.id
    try:
        cid = rc.primary.content.filter(content_type='text/plain', is_deleted=False, content_resource__location__startswith='https://diging').first().content_resource.id
    except AttributeError:
        print uri
        continue
    resource_map[uri] = (rid, cid)


'http://hdl.handle.net/10776/8147',
'http://hdl.handle.net/10776/8148',
'http://hdl.handle.net/10776/8146',
'http://hdl.handle.net/10776/3705',
'http://hdl.handle.net/10776/3704',
'http://hdl.handle.net/10776/3703',
'http://hdl.handle.net/10776/3706'

resource_text_defaults = {
    'title': resource.get('title'),
    'created': resource.get('created'),
    'repository': amphora,
    'repository_source_id': text_id,
    'addedBy_id': 1,
}

resource_text, _ = Text.objects.get_or_create(uri=resource['uri'], defaults=resource_text_defaults)
defaults = {
    'title': resource.get('title'),
    'created': resource.get('created'),
    'repository': amphora,
    'repository_source_id': content_id,
    'addedBy_id': 1,
    'content_type': content.get('content_type', None),
    'part_of': resource_text,
    'originalResource': getattr(resource.get('url'), 'value', None),
}

for uri, idents in uri_source_map.iteritems():
    text_id, content_id = tuple(idents)
    content = manager.content(id=int(content_id))
    resource = manager.resource(id=int(text_id))
    resource_text_defaults = {
        'title': resource.get('title'),
        'created': resource.get('created'),
        'repository': amphora,
        'repository_source_id': text_id,
        'addedBy': user,
    }
    resource_text, _ = Text.objects.get_or_create(uri=resource['uri'], defaults=resource_text_defaults)
    defaults = {
        'title': resource.get('title'),
        'created': resource.get('created'),
        'repository': amphora,
        'repository_source_id': content_id,
        'addedBy': user,
        'content_type': content.get('content_type', None),
        'part_of': resource_text,
        'originalResource': getattr(resource.get('url'), 'value', None),
    }
    text, _ = Text.objects.get_or_create(uri=content['uri'], defaults=defaults)
    text_id_map[uri] = text.id
    print uri

doc_positions_failed = []
doc_position_map = {}
for i, datum in enumerate(doc_positions):
    try:
        doc_position_map[datum['pk']] = DocumentPosition.objects.create(
            occursIn_id = text_id_map[text_uri_lookup[datum['fields']['occursIn']]],
            position_value = datum['fields']['position_value'],
            position_type = datum['fields']['position_type']
        ).id
        print '\r', i, doc_position_map[datum['pk']],
    except:
        doc_positions_failed.append(datum)

dateappellations_failed = []
date_appellation_map = {}
for i, datum in enumerate(dateappellations):
    try:
        submittedWith = datum['fields']['submittedWith']
        if submittedWith is not None:
            submittedWith = quadriga_lookup[submittedWith]
        position = datum['fields']['position']
        if position is not None:
            position = doc_position_map[position]
        date_appellation_map[datum['pk']] = DateAppellation.objects.create(
            stringRep = datum['fields']['stringRep'],
            created = datum['fields']['created'],
            submittedOn = datum['fields']['submittedOn'],
            occursIn_id = text_id_map[text_uri_lookup[datum['fields']['occursIn']]],
            submitted = datum['fields']['submitted'],
            month = datum['fields']['month'],
            submittedWith_id = submittedWith,
            createdBy_id = user_lookup[datum['fields']['createdBy']],
            year = datum['fields']['year'],
            position_id = position,
            day = datum['fields']['day'],
        ).id
        print '\r', i, date_appellation_map[datum['pk']],
    except:
        dateappellations_failed.append(datum)


appellations_failed = []
appellation_map = {}
for i, datum in enumerate(appellation_data):
    try:
        submittedWith = datum['fields']['submittedWith']
        if submittedWith is not None:
            submittedWith = quadriga_lookup[submittedWith]
        position = datum['fields']['position']
        if position is not None:
            position = doc_position_map[position]
        appellation_map[datum['pk']] = Appellation.objects.create(
            interpretation_id = concept_id_map[datum['fields']['interpretation']],
            stringRep = datum['fields']['stringRep'],
            created = datum['fields']['created'],
            submittedOn = datum['fields']['submittedOn'],
            occursIn_id = text_id_map[text_uri_lookup[datum['fields']['occursIn']]],
            asPredicate = datum['fields']['asPredicate'],
            submitted = datum['fields']['submitted'],
            createdBy_id = user_lookup[datum['fields']['createdBy']],
            position_id = position,
            submittedWith_id = submittedWith,
        ).id
        print '\r', i, appellation_map[datum['pk']],
    except:
        appellations_failed.append(datum)


submittedWith = datum['fields']['submittedWith']
if submittedWith is not None:
    submittedWith = quadriga_lookup[submittedWith]


position = datum['fields']['position']
if position is not None:
    position = doc_position_map[position]


appellation_map[datum['pk']] = Appellation.objects.create(
    interpretation_id = concept_id_map[datum['fields']['interpretation']],
    stringRep = datum['fields']['stringRep'],
    created = datum['fields']['created'],
    submittedOn = datum['fields']['submittedOn'],
    occursIn_id = text_id_map[text_uri_lookup[datum['fields']['occursIn']]],
    asPredicate = datum['fields']['asPredicate'],
    submitted = datum['fields']['submitted'],
    createdBy_id = user_lookup[datum['fields']['createdBy']],
    position_id = position,
    submittedWith_id = submittedWith,
).id



relationset_map = {}
relationsets_failed = []
for i, datum in enumerate(relationset_data):
    try:
        submittedWith = datum['fields']['submittedWith']
        if submittedWith is not None:
            submittedWith = quadriga_lookup[submittedWith]
        template = datum['fields']['template']
        if template is not None:
            template = rtemplate_map[template]
        relationset_map[datum['pk']] = RelationSet.objects.create(
            template_id = template,
            created = datum['fields']['created'],
            submittedOn = datum['fields']['submittedOn'],
            occursIn_id = text_id_map[text_uri_lookup[datum['fields']['occursIn']]],
            submitted = datum['fields']['submitted'],
            createdBy_id = user_lookup[datum['fields']['createdBy']],
            representation = datum['fields']['representation'],
            submittedWith_id = submittedWith,
            pending = datum['fields']['pending'],
        ).id
        print '\r', i, relationset_map[datum['pk']],
    except:
        relationsets_failed.append(datum)


def proc_relation(datum):
    with transaction.atomic():
        part_of = datum['fields']['part_of']
        if part_of is not None:
            part_of = relationset_map[part_of]
        submittedWith = datum['fields']['submittedWith']
        if submittedWith is not None:
            submittedWith = quadriga_lookup[submittedWith]
        relation = Relation.objects.create(
            part_of_id = part_of,
            created = datum['fields']['created'],
            submittedOn = datum['fields']['submittedOn'],
            occursIn_id = text_id_map[text_uri_lookup[datum['fields']['occursIn']]],
            predicate_id = appellation_map[datum['fields']['predicate']],
            submitted = datum['fields']['submitted'],
            createdBy_id = user_lookup[datum['fields']['createdBy']],
            submittedWith_id = submittedWith,
        )
        bounds = datum['fields']['bounds']
        if bounds is not None:
            for key, value in temporal_data[bounds].iteritems():
                if value:
                    uri = settings.TEMPORAL_PREDICATES[key]
                    appellation = Appellation.objects.create(
                        created = datum['fields']['created'],
                        createdBy_id = user_lookup[datum['fields']['createdBy']],
                        occursIn_id = text_id_map[text_uri_lookup[datum['fields']['occursIn']]],
                        submittedWith_id = submittedWith,
                        submitted = datum['fields']['submitted'],
                        submittedOn = datum['fields']['submittedOn'],
                        interpretation = Concept.objects.get_or_create(uri=uri)[0],
                    )
                    dateappellation = DateAppellation.objects.create(
                        created = datum['fields']['created'],
                        createdBy_id = user_lookup[datum['fields']['createdBy']],
                        occursIn_id = text_id_map[text_uri_lookup[datum['fields']['occursIn']]],
                        submittedWith_id = submittedWith,
                        submitted = datum['fields']['submitted'],
                        submittedOn = datum['fields']['submittedOn'],
                    )
                    for p, verb in enumerate(['year', 'month', 'day']):
                        try:
                            v = value[p]
                        except IndexError:
                            break
                        setattr(dateappellation, verb, v)
                    dateappellation.save()
                    Relation.objects.create(
                        source_content_object=relation,
                        predicate = appellation,
                        object_content_object=dateappellation,
                        part_of_id = part_of,
                        created = datum['fields']['created'],
                        createdBy_id = user_lookup[datum['fields']['createdBy']],
                        submittedOn = datum['fields']['submittedOn'],
                        occursIn_id = text_id_map[text_uri_lookup[datum['fields']['occursIn']]],
                    )
    return relation


def get_target(ctype_id, pk):
    model = ctypes[ctype_id]
    if model == 'relation':
        return relation_map[pk]
    elif model == 'appellation':
        klass = Appellation
        lookup = appellation_map
    elif model == 'dateappellation':
        klass = DateAppellation
        lookup = date_appellation_map
    return klass.objects.get(pk=lookup[pk])


relation_map = {}
relations_failed = []
for i, datum in enumerate(relation_data[1:]):
    try:
        relation_map[datum['pk']] = proc_relation(datum)
        print '\r', i, relation_map[datum['pk']],
    except:
        relations_failed.append(datum)


for datum in relation_data:
    so_ctype = datum['fields']['source_content_type']
    ob_ctype = datum['fields']['object_content_type']
    so_id = datum['fields']['source_object_id']
    ob_id = datum['fields']['object_object_id']
    relation = relation_map[datum['pk']]
    relation.source_content_object = get_target(so_ctype, so_id)
    relation.object_content_object = get_target(ob_ctype, ob_id)
    relation.save()
    print '\r', relation.id,


for pk in relationset_map.values():
    relationset = RelationSet.objects.get(pk=pk)
    for cp in relationset.terminal_nodes.all():
        if cp.label == '' or cp.label is None:
            relationset.terminal_nodes.remove(cp)
            print cp
