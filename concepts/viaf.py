import requests
import json
from lxml import etree

class Viaf:
    def __init__(self):
        self.namespace = 'http://viaf.org/viaf/terms#'
        self.endpoint = 'http://viaf.org'

    def search(self, params):
        url = f'{self.endpoint}/viaf/AutoSuggest'
        params = { 'query': params['q'] }
        response = requests.get(url=url, params=params)
        concepts = json.loads(response.content)['result']
        results = []
        if concepts:
            for concept in concepts:
                concept_type = concept['nametype']
                identifier = concept['viafid']
                result = {
                    'name': concept['term'],
                    'description': concept['displayForm'],
                    'concept_type': f'viaf:{concept_type}',
                    'identifier': f'{self.endpoint}/viaf/{identifier}',
                    'local_identifier': concept['viafid']
                }
                results.append(result)

        return results

    def type(self, identifier):
        raise NotImplementedError

    def get(self, identifier):
        url = f'{self.endpoint}/viaf/{identifier}/viaf.xml'
        params = {'local_id': identifier}
        response = requests.get(url=url, params=params)
        root = etree.fromstring(response.content)

        concept_type = root.find(f'{{{self.namespace}}}nameType').text
        viaf_id = root.find(f'{{{self.namespace}}}viafID').text
        
        main_headings = root.find(f'{{{self.namespace}}}mainHeadings')
        text, sid, data = None, None, None
        identities = []
        if main_headings:
            data = main_headings.findall(f'{{{self.namespace}}}data')
        
        if data and len(data) > 0:
            text = data[0].find(f'{{{self.namespace}}}text').text
            for item in data:
                sources = item.find(f'{{{self.namespace}}}sources')
                sids = sources.findall(f'{{{self.namespace}}}sid')
                for sid in sids:
                    identities.append(sid.text)

        return {
            'concept_type': concept_type,
            'name': text,
            'identifier': f'{self.endpoint}/viaf/{viaf_id}',
            'local_identifier': viaf_id,
            'identities': identities
        }
