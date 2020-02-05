import requests,json
import xml.etree.ElementTree as ET
from requests.auth import HTTPBasicAuth


class Conceptpower:
    """
    Provides simple access to the `Conceptpower
    <http://conceptpower.sourceforge.net/>`_ API.

    Set :prop:`.endpoint` and :prop:`.namespace` when subclassing
    :class:`.Conceptpower` or by passing them as ``kwargs`` to the constructor.

    Parameters
    ----------
    kwargs : kwargs
        Set :prop:`.endpoint` and :prop:`.namespace` by passing ``endpoint``
        and ``namespace`` kwargs, respectively. This will have no effect if
        those properties are set in the class definition (e.g. when subclassing
        :class:`.Conceptpower`\.
    """

    # Default behavior is to leave these to the constructor.
    endpoint = None
    namespace = None

    def __init__(self, **kwargs):
        # Give first priority to the class definition, if endpoint or namespace
        #  are defined (and not None).
        if self.endpoint is None:
            self.endpoint = kwargs.get(
                "endpoint", "http://chps.asu.edu/conceptpower/rest/")

        if self.namespace is None:
            self.namespace = kwargs.get(
               "namespace", "{http://www.digitalhps.org/}")

    def search (self, query, pos='Noun'):
        """
        Search for a concept by lemma.

        Parameters
        ----------
        query : str
            Search term.
        pos : str
            (default: 'Noun') Part of speech: Noun, Verb, etc.

        Returns
        -------
        results : list

        Example
        -------
        >>> pprint (cp.search("Bradshaw"))
        [{'conceptList': 'Persons',
          'description': 'Plant ecologist',
          'id': 'http://www.digitalhps.org/concepts/066efc74-8710-4a1f-9111-3a27d880438e',
          'lemma': 'Anthony David Bradshaw (1926-2008)',
          'pos': 'noun',
          'type': 'E21 Person'},
         {'conceptList': 'Persons',
          'description': 'Botanist at the University of Exeter',
          'id': 'http://www.digitalhps.org/concepts/CONe5b55803-1ef6-4abe-b81c-1493e97421df',
          'lemma': 'Margaret E. Bradshaw',
          'pos': 'noun',
          'type': 'E21 Person'},
         {'conceptList': 'Publications',
          'description': 'Bradshaw, Anthony David. 1965. "The evolutionary significance of phenotypic plasticity in plants." Advances in Genetics 13: 115-155.',
          'id': 'http://www.digitalhps.org/concepts/CON76832db2-7abb-4c77-b08e-239017b6a585',
          'lemma': 'Bradshaw 1965',
          'pos': 'noun',
          'type': 'E28 Conceptual Object '},
         {'conceptList': 'Phenotypic Plasticity',
          'description': None,
          'id': 'http://www.digitalhps.org/concepts/72ec32b4-2a20-4d26-ab8f-a173f067542d',
          'lemma': 'Anthony D. Bradshaw',
          'pos': 'noun',
          'type': None}]
        """

        url = "{0}ConceptLookup/{1}/{2}".format(self.endpoint, query, pos)
        response = requests.get(url, headers = { 'Accept': 'application/xml' })
        if response.status_code != 200:
            return []
        root = ET.fromstring(response.content)
        conceptEntries = root.findall("{0}conceptEntry".format(self.namespace))

        results = []
        for conceptEntry in conceptEntries:
            datum = {}
            for node in conceptEntry:
                datum[node.tag.replace(self.namespace, '')] = node.text
                if node.tag == '{0}type'.format(self.namespace):
                    datum['type_id'] = node.get('type_id')
                    datum['type_uri'] = node.get('type_uri')
            results.append(datum)
        return results

    def get(self, uri):
        """
        Retrieve information (by ID or URI) about a concept.

        Parameters
        ----------
        uri : str
            The full Conceptpower URI, or an ID, as string. For example:
            http://www.digitalhps.org/CON7971a85a-49e1-424d-84e6-697262bd2510

        Returns
        -------
        data : dict

        Example
        -------
        >>> pprint (cp.get("http://www.digitalhps.org/concepts/CON536b243d-3c71-4a5c-ab79-3c7f12765b3f"))
        {'conceptList': 'Persons',
         'description': 'A professor at the Cambridge Botany School',
         'id': 'http://www.digitalhps.org/concepts/CON536b243d-3c71-4a5c-ab79-3c7f12765b3f',
         'lemma': 'Sir Harry Godwin',
         'pos': 'noun',
         'type': 'E21 Person',
         'type_id': '986a7cc9-c0c1-4720-b344-853f08c136ab',
         'type_uri': 'http://www.digitalhps.org/types/TYPE_986a7cc9-c0c1-4720-b344-853f08c136ab'}
        """

        url = "{0}Concept?id={1}".format(self.endpoint, uri)
        response = requests.get(url, headers = { 'Accept': 'application/xml' })
        root = ET.fromstring(response.content)
        data = {}
        conceptEntries = root.findall("{0}conceptEntry".format(self.namespace))

        if len(conceptEntries) > 0:
            conceptEntry = conceptEntries[0]

            for snode in conceptEntry:
                value = snode.text
                if snode.tag == '{0}type'.format(self.namespace):
                    data['type_id'] = snode.get('type_id')
                    data['type_uri'] = snode.get('type_uri')
                elif snode.tag == '{0}equal_to'.format(self.namespace):
                    if value:
                        value = value.split(',')
                data[snode.tag.replace(self.namespace, '')] = value

        return data

    def get_type(self, uri):
        """
        Retrieve information (by ID or URI) about a type.

        Parameters
        ----------
        uri : str
            The full Conceptpower URI, or an ID, as string. For example:
            http://www.digitalhps.org/types/TYPE_986a7cc9-c0c1-4720-b344-853f08c136ab

        Returns
        -------
        data : dict
        """

        url = "{0}Type?id={1}".format(self.endpoint, uri)
        root = ET.fromstring(requests.get(url, headers = { 'Accept': 'application/xml' }).content)
        conceptEntries = root.findall("{0}type_entry".format(self.namespace))
        data = {}

        if len(conceptEntries) > 0:
            conceptEntry = conceptEntries[0]

            for snode in conceptEntry:
                data[snode.tag.replace(self.namespace, '')] = snode.text
                if snode.tag == '{0}supertype'.format(self.namespace):
                    data['supertype_id'] = snode.get('supertype_id')
                    data['supertype_uri'] = snode.get('supertype_uri')

        return data

    def create(self, user, password, label, pos, conceptlist, description,
               concepttype, synonym_ids=[], equal_uris=[], similar_uris=[]):
        """
        Add a new concept.

        Refer to documentation at
        http://diging.github.io/conceptpower/doc/rest_add_concepts.html.

        Parameters
        -----------
        user : str
            UserId of the person who wants to add concept.
        password : str
            Password of the person who wants to add concept.
        label : str
            Name of the concept.
        pos : str
            Part of speech of the concept.
        conceptlist : str
            Name of the conceptlist concept belongs to.
        description : str
            Description of the concept.
        concepttype : str
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

        auth = HTTPBasicAuth(user,password)
        rest_url = "{0}concept/add".format(self.endpoint)

        concept_data = {
            "word": label,
            "pos": pos,
            "conceptlist": conceptlist,
            "description": description,
            "type": concepttype,
            "synonymids": synonym_ids,
            "equals": equal_uris,
            "similar": similar_uris
        }

        r = requests.post(url=rest_url, data=json.dumps(concept_data), auth=auth)


        if r.status_code != requests.codes.ok:
            raise RuntimeError(r.status_code, r.text)

        # Returned data after successful response
        return r.json()
