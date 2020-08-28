import requests
import json
from requests.auth import HTTPBasicAuth
from lxml import etree
from django.conf import settings

class ConceptPower:
    def __init__(self, namespace):
        self.namespace = namespace
        self.endpoint = settings.CONCEPTPOWER_ENDPOINT
        self.username = settings.CONCEPTPOWER_USERID
        self.password = settings.CONCEPTPOWER_PASSWORD
    
    def search(self, params):
        url = f'{self.endpoint}/ConceptSearch'
        params = {
            'word': params['q'],
            'pos': params['pos'],
            'number_of_records_per_page': params['limit']
        }
        response = requests.get(url=url, params=params)
        root = etree.fromstring(response.content)
        results = []
        for child in root.findall(f'{{{self.namespace}}}conceptEntry'):
            data = self._parse_concept(child)
            results.append(data)

        return results

    def type(self, identifier):
        url = f'{self.endpoint}/Type'
        params = {
            'id': identifier
        }
        response = requests.get(url=url, params=params)
        root = etree.fromstring(response.content)
        
        type_entries = root.findall(f'{{{self.namespace}}}type_entry')
        data = {}

        if len(type_entries) > 0:
            type_entry = type_entries[0]
            data['name'] = type_entry.find(f'{{{self.namespace}}}type').text
            data['description'] = type_entry.find(f'{{{self.namespace}}}description').text
            
            identity = type_entry.find(f'{{{self.namespace}}}matches').text
            identities = None
            if identity:
                identities = [identity]
            data['identities'] = identities

        return data

    def get(self, identifier):
        url = f'{self.endpoint}/Concept'
        params = {
            'id': identifier
        }
        response = requests.get(url=url, params=params)
        root = etree.fromstring(response.content)

        concept_entries = root.findall(f'{{{self.namespace}}}conceptEntry')

        if len(concept_entries) > 0:
            entry = concept_entries[0]
            data = self._parse_concept(entry)
            return data
        
        return None

    def create(self, label, pos, conceptlist, description,
               concept_type, synonym_ids=[], equal_uris=[], similar_uris=[]):
        """
        Add a new concept.

        Refer to documentation at
        http://diging.github.io/conceptpower/doc/rest_add_concepts.html.

        Parameters
        -----------
        label : str
            Name of the concept.
        pos : str
            Part of speech of the concept.
        conceptlist : str
            Name of the conceptlist concept belongs to.
        description : str
            Description of the concept.
        concept_type : str
            Type of the concept.
        synonymids : list
            Ids of synonyms for the new concept.
        equal_uris : list
            URIs of concepts that are equal to the new concept.
        similar_uris : list
            URIs of concepts that are similar to the new concept.

        Returns
        -------
        data : dict
            When the concept has been successfully added, data is returned.
        """
        auth = HTTPBasicAuth(self.username, self.password)
        url = f'{self.endpoint}/concept/add'
        data = {
            "word": label,
            "pos": pos,
            "conceptlist": conceptlist,
            "description": description,
            "type": concept_type,
            "synonymids": synonym_ids,
            "equals": equal_uris,
            "similar": similar_uris
        }

        response = request.post(url=url, data=json.dumps(data), auth=auth)

        if response.status_code != 200:
            raise RuntimeError(response.status_code, response.text)

        return response.json()

    def _parse_concept(self, entry):
        name = entry.find(f'{{{self.namespace}}}lemma').text
        description = entry.find(f'{{{self.namespace}}}description').text
        local_identifier = entry.find(f'{{{self.namespace}}}id').text
        identity = entry.find(f'{{{self.namespace}}}equal_to').text
        
        # Find concept URI
        concept_type_attr = entry.find(f'{{{self.namespace}}}type').attrib
        concept_type = None
        if concept_type_attr:
            concept_type = concept_type_attr.get('type_uri', None)
        
        # Find identifier
        id_attr = entry.find(f'{{{self.namespace}}}id').attrib
        identifier = None
        identities = None
        if id_attr:
            identifier = id_attr.get('concept_uri', None)
        if identity:
            identities = [identity]
        
        data = {
            'name': name,
            'description': description,
            'concept_type': concept_type,
            'identifier': identifier,
            'local_identifier': local_identifier,
            'identities': identities
        }
        return data
