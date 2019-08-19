from django.test import TestCase
from django.db.models.signals import post_save
from concepts.authorities import resolve, search
from concepts.models import Concept, Type
from concepts.signals import concept_post_save_receiver
import mock, json
from concepts.lifecycle import *


class MockResponse(object):
    def __init__(self, content, status_code=200):
        self.content = content
        self.status_code = status_code

    def json(self):
        return json.loads(self.content)


def disconnect_signal(signal, receiver, sender):
    disconnect = getattr(signal, 'disconnect')
    disconnect(receiver, sender)


def reconnect_signal(signal, receiver, sender):
    connect = getattr(signal, 'connect')
    connect(receiver, sender=sender)


class TestConceptLifeCycle(TestCase):
    """
    The :class:`.ConceptLifecycle` guides :class:`.Concept`\s through their
    various trials and tribulations.
    """
    def setUp(self):
        disconnect_signal(post_save, concept_post_save_receiver, Concept)

    def test_is_native(self):
        """
        A :class:`.ConceptLifecycle` should know if its constituent is from
        Conceptpower or not.
        """

        instance = Concept.objects.create(
            label = "Test",
            uri = "http://asdf.com/test",
        )
        manager = ConceptLifecycle(instance)
        self.assertFalse(manager.is_native)    # A dynamic property!

        instance = Concept.objects.create(
            label = "goat",
            uri = "http://www.digitalhps.org/concepts/WID-02416519-N-01-goat",
        )
        manager = ConceptLifecycle(instance)
        self.assertTrue(manager.is_native)    # A dynamic property!

    def test_is_created(self):
        """
        A :class:`.ConceptLifecycle` should know if its constituent was created
        by a user or not.
        """
        instance = Concept.objects.create(
            label = "User created nonsense",
            uri = "http://vogonweb.net/12345",
        )
        manager = ConceptLifecycle(instance)
        self.assertTrue(manager.is_created)

        instance = Concept.objects.create(
            label = "goat",
            uri = "http://www.digitalhps.org/concepts/WID-02416519-N-01-goat",
        )
        manager = ConceptLifecycle(instance)
        self.assertFalse(manager.is_created)

    def test_native_default_state(self):
        """
        Native concepts (from Conceptpower) should be resolved immediately.
        """
        instance = Concept.objects.create(
            label = "goat",
            uri = "http://www.digitalhps.org/concepts/WID-02416519-N-01-goat",
        )
        manager = ConceptLifecycle(instance)
        self.assertEqual(manager.default_state, Concept.RESOLVED)

    def test_external_default_state(self):
        """
        Non-native external concepts (from other Goat authorities) should be
        approved immediately. They do exist already, after all.
        """
        instance = Concept.objects.create(
            label = "Test",
            uri = "http://viaf.org/viaf/12345",
        )
        manager = ConceptLifecycle(instance)
        self.assertEqual(manager.default_state, Concept.APPROVED)

    def test_user_created_default_state(self):
        """
        User-created concepts should be PENDING by default; they require admin
        review.
        """
        instance = Concept.objects.create(
            label = "Test",
            uri = "http://vogonweb.net/12345",
        )
        manager = ConceptLifecycle(instance)
        self.assertEqual(manager.default_state, Concept.PENDING)

    @mock.patch("requests.get")
    def test_get_similar_suggestions(self, mock_get):
        """
        The :class:`.ConceptLifecycle` should handle retrieving suggestions.

        We're not creating new :class:`.Concept`\s at this point, just getting
        data.
        """

        instance = Concept.objects.create(
            label = "User created nonsense",
            uri = "http://vogonweb.net/12345",
        )
        manager = ConceptLifecycle(instance)

        mock_get.return_value = MockResponse("""<conceptpowerReply xmlns:digitalHPS="http://www.digitalhps.org/">
                <digitalHPS:conceptEntry>
                <digitalHPS:id concept_id="CON76832db2-7abb-4c77-b08e-239017b6a585" concept_uri="http://www.digitalhps.org/concepts/CON76832db2-7abb-4c77-b08e-239017b6a585">http://www.digitalhps.org/concepts/CON76832db2-7abb-4c77-b08e-239017b6a585</digitalHPS:id>
                <digitalHPS:lemma>Bradshaw 1965</digitalHPS:lemma>
                <digitalHPS:pos>noun</digitalHPS:pos>
                <digitalHPS:description>Bradshaw, Anthony David. 1965. "The evolutionary significance of phenotypic plasticity in plants." Advances in Genetics 13: 115-155.</digitalHPS:description>
                <digitalHPS:conceptList>Publications</digitalHPS:conceptList>
                <digitalHPS:creator_id>erick</digitalHPS:creator_id>
                <digitalHPS:equal_to/>
                <digitalHPS:modified_by/>
                <digitalHPS:similar_to/>
                <digitalHPS:synonym_ids/>
                <digitalHPS:type type_id="94d05eb7-bcee-4f4b-b18e-819dd1ffb20a" type_uri="http://www.digitalhps.org/types/TYPE_94d05eb7-bcee-4f4b-b18e-819dd1ffb20a">E28 Conceptual Object</digitalHPS:type>
                <digitalHPS:deleted>false</digitalHPS:deleted>
                <digitalHPS:wordnet_id/>
                <digitalHPS:alternativeIds>
                <digitalHPS:id concept_id="CON76832db2-7abb-4c77-b08e-239017b6a585" concept_uri="http://www.digitalhps.org/concepts/CON76832db2-7abb-4c77-b08e-239017b6a585">http://www.digitalhps.org/concepts/CON76832db2-7abb-4c77-b08e-239017b6a585</digitalHPS:id>
                </digitalHPS:alternativeIds>
                </digitalHPS:conceptEntry>
                <digitalHPS:conceptEntry>
                <digitalHPS:id concept_id="WID-11074284-N-03-Christopher_William_Bradshaw_Isherwood" concept_uri="http://www.digitalhps.org/concepts/WID-11074284-N-03-Christopher_William_Bradshaw_Isherwood">http://www.digitalhps.org/concepts/WID-11074284-N-03-Christopher_William_Bradshaw_Isherwood</digitalHPS:id>
                <digitalHPS:lemma>christopher william bradshaw isherwood</digitalHPS:lemma>
                <digitalHPS:pos>noun</digitalHPS:pos>
                <digitalHPS:description>United States writer (born in England) whose best known novels portray Berlin in the 1930's and who collaborated with W. H. Auden in writing plays in verse (1904-1986)</digitalHPS:description>
                <digitalHPS:conceptList>WordNet</digitalHPS:conceptList>
                <digitalHPS:creator_id/>
                <digitalHPS:equal_to/>
                <digitalHPS:modified_by/>
                <digitalHPS:similar_to/>
                <digitalHPS:synonym_ids>WID-11074284-N-01-Isherwood,WID-11074284-N-02-Christopher_Isherwood,</digitalHPS:synonym_ids>
                <digitalHPS:type/>
                <digitalHPS:deleted>false</digitalHPS:deleted>
                <digitalHPS:wordnet_id>WID-11074284-N-03-Christopher_William_Bradshaw_Isherwood</digitalHPS:wordnet_id>
                <digitalHPS:alternativeIds>
                <digitalHPS:id concept_id="WID-11074284-N-03-Christopher_William_Bradshaw_Isherwood" concept_uri="http://www.digitalhps.org/concepts/WID-11074284-N-03-Christopher_William_Bradshaw_Isherwood">http://www.digitalhps.org/concepts/WID-11074284-N-03-Christopher_William_Bradshaw_Isherwood</digitalHPS:id>
                </digitalHPS:alternativeIds>
                </digitalHPS:conceptEntry>
                </conceptpowerReply>""")

        suggestions = manager.get_similar()
        self.assertIsInstance(suggestions, list)
        self.assertEqual(len(suggestions), 2)
        self.assertIsInstance(suggestions[0], ConceptData)
        self.assertEqual(suggestions[0].label, 'Bradshaw 1965')
        self.assertEqual(suggestions[0].uri, 'http://www.digitalhps.org/concepts/CON76832db2-7abb-4c77-b08e-239017b6a585')

    @mock.patch("requests.get")
    def test_get_matching_suggestions(self, mock_get):
        """
        The :class:`.ConceptLifecycle` should handle retrieving matching
        concepts. A matching concepts is a Conceptpower concept that wraps
        (via the equal_to field) an external concept (e.g. a VIAF entry).
        """

        instance = Concept.objects.create(
            label = "Test",
            uri = "http://viaf.org/viaf/12345",
        )
        manager = ConceptLifecycle(instance)

        mock_get.return_value = MockResponse("""<conceptpowerReply xmlns:digitalHPS="http://www.digitalhps.org/">
                <digitalHPS:conceptEntry>
                <digitalHPS:id concept_id="CON76832db2-7abb-4c77-b08e-239017b6a585" concept_uri="http://www.digitalhps.org/concepts/CON76832db2-7abb-4c77-b08e-239017b6a585">http://www.digitalhps.org/concepts/CON76832db2-7abb-4c77-b08e-239017b6a585</digitalHPS:id>
                <digitalHPS:lemma>Bradshaw 1965</digitalHPS:lemma>
                <digitalHPS:pos>noun</digitalHPS:pos>
                <digitalHPS:description>Bradshaw, Anthony David. 1965. "The evolutionary significance of phenotypic plasticity in plants." Advances in Genetics 13: 115-155.</digitalHPS:description>
                <digitalHPS:conceptList>Publications</digitalHPS:conceptList>
                <digitalHPS:creator_id>erick</digitalHPS:creator_id>
                <digitalHPS:equal_to/>
                <digitalHPS:modified_by/>
                <digitalHPS:similar_to/>
                <digitalHPS:synonym_ids/>
                <digitalHPS:type type_id="94d05eb7-bcee-4f4b-b18e-819dd1ffb20a" type_uri="http://www.digitalhps.org/types/TYPE_94d05eb7-bcee-4f4b-b18e-819dd1ffb20a">E28 Conceptual Object</digitalHPS:type>
                <digitalHPS:deleted>false</digitalHPS:deleted>
                <digitalHPS:wordnet_id/>
                <digitalHPS:alternativeIds>
                <digitalHPS:id concept_id="CON76832db2-7abb-4c77-b08e-239017b6a585" concept_uri="http://www.digitalhps.org/concepts/CON76832db2-7abb-4c77-b08e-239017b6a585">http://www.digitalhps.org/concepts/CON76832db2-7abb-4c77-b08e-239017b6a585</digitalHPS:id>
                </digitalHPS:alternativeIds>
                </digitalHPS:conceptEntry>
            </conceptpowerReply>""")

        matches = manager.get_matching()
        self.assertIsInstance(matches, list)
        self.assertEqual(len(matches), 1)
        self.assertIsInstance(matches[0], ConceptData)
        self.assertEqual(matches[0].label, 'Bradshaw 1965')
        self.assertEqual(matches[0].uri, 'http://www.digitalhps.org/concepts/CON76832db2-7abb-4c77-b08e-239017b6a585')

    def test_create(self):
        """
        The :class:`.ConceptLifecycle` can create new :class:`.Concept`
        instances.
        """

        manager = ConceptLifecycle.create(
            label = "goat",
            uri = "http://www.digitalhps.org/concepts/WID-02416519-N-01-goat"
        )
        self.assertIsInstance(manager, ConceptLifecycle)
        self.assertIsInstance(manager.instance, Concept)
        self.assertEqual(manager.instance.label, "goat")
        self.assertEqual(manager.instance.uri, "http://www.digitalhps.org/concepts/WID-02416519-N-01-goat")

    def test_cannot_merge_resolved_concepts(self):
        """
        If a :class:`.Concept` is resolved, it can't be merged with any other
        concepts.
        """
        manager = ConceptLifecycle.create(
            label = "goat",
            uri = "http://www.digitalhps.org/concepts/WID-02416519-N-01-goat"
        )

        with self.assertRaises(ConceptLifecycleException):
            manager.merge_with('http://www.digitalhps.org/concepts/WID-02416519-N-02-goat')

    @mock.patch("requests.get")
    def test_merge_with_conceptpower(self, mock_get):
        """
        A non-native :class:`.Concept` can be merged with an existing native
        concept that may or may not reside locally.
        """
        mock_get.return_value = MockResponse("""<conceptpowerReply xmlns:digitalHPS="http://www.digitalhps.org/">
                <digitalHPS:conceptEntry>
                <digitalHPS:id concept_id="CON76832db2-7abb-4c77-b08e-239017b6a585" concept_uri="http://www.digitalhps.org/concepts/CON76832db2-7abb-4c77-b08e-239017b6a585">http://www.digitalhps.org/concepts/CON76832db2-7abb-4c77-b08e-239017b6a585</digitalHPS:id>
                <digitalHPS:lemma>Bradshaw 1965</digitalHPS:lemma>
                <digitalHPS:pos>noun</digitalHPS:pos>
                <digitalHPS:description>Bradshaw, Anthony David. 1965. "The evolutionary significance of phenotypic plasticity in plants." Advances in Genetics 13: 115-155.</digitalHPS:description>
                <digitalHPS:conceptList>Publications</digitalHPS:conceptList>
                <digitalHPS:creator_id>erick</digitalHPS:creator_id>
                <digitalHPS:equal_to/>
                <digitalHPS:modified_by/>
                <digitalHPS:similar_to/>
                <digitalHPS:synonym_ids/>
                <digitalHPS:type type_id="94d05eb7-bcee-4f4b-b18e-819dd1ffb20a" type_uri="http://www.digitalhps.org/types/TYPE_94d05eb7-bcee-4f4b-b18e-819dd1ffb20a">E28 Conceptual Object</digitalHPS:type>
                <digitalHPS:deleted>false</digitalHPS:deleted>
                <digitalHPS:wordnet_id/>
                <digitalHPS:alternativeIds>
                <digitalHPS:id concept_id="CON76832db2-7abb-4c77-b08e-239017b6a585" concept_uri="http://www.digitalhps.org/concepts/CON76832db2-7abb-4c77-b08e-239017b6a585">http://www.digitalhps.org/concepts/CON76832db2-7abb-4c77-b08e-239017b6a585</digitalHPS:id>
                </digitalHPS:alternativeIds>
                </digitalHPS:conceptEntry>
                </conceptpowerReply>""")

        manager = ConceptLifecycle.create(
            label = "Test",
            uri = "http://viaf.org/viaf/12345",
            resolve = False
        )
        instance = manager.instance
        
        manager.merge_with('http://www.digitalhps.org/concepts/CON76832db2-7abb-4c77-b08e-239017b6a585')
        instance.refresh_from_db()
        self.assertTrue(instance.merged_with is not None)
        self.assertIsInstance(instance.merged_with, Concept)
        self.assertEqual(instance.concept_state, Concept.MERGED)
        self.assertEqual(instance.merged_with.uri, 'http://www.digitalhps.org/concepts/CON76832db2-7abb-4c77-b08e-239017b6a585')

    @mock.patch("requests.post")
    def test_add(self, mock_post):
        """
        When a created :class:`.Concept` is "added" to Conceptpower, a new
        :class:`.Concept` instance should be created to represent that new
        concept, and the created :class:`.Concept` instance should be merged
        with the new instance.
        """

        mock_post.return_value = MockResponse("""{
                    "pos": "noun",
                    "conceptlist": "Persons",
                    "description": "Soft kitty, sleepy kitty, little ball of fur.",
                    "id": "CONkLHTIeUQqM7m",
                    "type": "0d5d1992-957b-49b6-ad7d-117daaf28108",
                    "word": "kitty",
                    "uri": "http:\/\/www.digitalhps.org\/concepts\/CONkLHTIeUQqM7m"
                }""")

        manager = ConceptLifecycle.create(
            label = "Test",
            uri = "http://vogonweb.net/test",
            typed = Type.objects.get_or_create(uri='viaf:personal')[0]
        )
        concept = manager.instance

        manager.add()
        concept.refresh_from_db()

        self.assertEqual(concept.concept_state, Concept.MERGED)
        self.assertIsInstance(concept.merged_with, Concept)
        self.assertEqual(concept.merged_with.uri, "http://www.digitalhps.org/concepts/CONkLHTIeUQqM7m")
        self.assertEqual(concept.merged_with.concept_state, Concept.RESOLVED)

    @mock.patch("requests.get")
    @mock.patch("requests.post")
    def test_add_wrapper(self, mock_post, mock_get):
        """
        For non-created :class:`.Concept`\s, the only difference is that the
        new Conceptpower entry should have ``equal_to`` set to the concept URI.
        """
        mock_post.return_value = MockResponse("""{
                    "equal_to": "http://viaf.org/viaf/12345",
                    "pos": "noun",
                    "conceptlist": "Persons",
                    "description": "Soft kitty, sleepy kitty, little ball of fur.",
                    "id": "CONnN9sURrONpUs",
                    "type": "0d5d1992-957b-49b6-ad7d-117daaf28108",
                    "word": "kitty2",
                    "uri": "http:\/\/www.digitalhps.org\/concepts\/CONnN9sURrONpUs"
                }""")

        mock_get.return_value = MockResponse("""
                <conceptpowerReply xmlns:digitalHPS="http://www.digitalhps.org/">
                <digitalHPS:conceptEntry>
                <digitalHPS:id concept_id="CONnN9sURrONpUs" concept_uri="http://www.digitalhps.org/concepts/CONnN9sURrONpUs">http://www.digitalhps.org/concepts/CONnN9sURrONpUs</digitalHPS:id>
                <digitalHPS:lemma>kitty2</digitalHPS:lemma>
                <digitalHPS:pos>noun</digitalHPS:pos>
                <digitalHPS:description>Soft kitty, sleepy kitty, little ball of fur.</digitalHPS:description>
                <digitalHPS:conceptList>Persons</digitalHPS:conceptList>
                <digitalHPS:creator_id>test</digitalHPS:creator_id>
                <digitalHPS:equal_to>http://viaf.org/viaf/12345</digitalHPS:equal_to>
                <digitalHPS:modified_by>test</digitalHPS:modified_by>
                <digitalHPS:similar_to/>
                <digitalHPS:synonym_ids/>
                <digitalHPS:type type_id="0d5d1992-957b-49b6-ad7d-117daaf28108" type_uri="http://www.digitalhps.org/types/TYPE_0d5d1992-957b-49b6-ad7d-117daaf28108">E12 Production</digitalHPS:type>
                <digitalHPS:deleted>false</digitalHPS:deleted>
                <digitalHPS:wordnet_id/>
                <digitalHPS:alternativeIds>
                <digitalHPS:id concept_id="CONnN9sURrONpUs" concept_uri="http://www.digitalhps.org/concepts/CONnN9sURrONpUs">http://www.digitalhps.org/concepts/CONnN9sURrONpUs</digitalHPS:id>
                </digitalHPS:alternativeIds>
                </digitalHPS:conceptEntry>
                </conceptpowerReply>""")

        manager = ConceptLifecycle.create(
            label = "Test",
            uri = "http://viaf.org/viaf/12345",
            resolve = False,
            typed = Type.objects.get_or_create(uri='viaf:personal')[0]
        )
        concept = manager.instance

        manager.add()
        concept.refresh_from_db()

        self.assertEqual(concept.concept_state, Concept.MERGED)
        self.assertIsInstance(concept.merged_with, Concept)
        self.assertEqual(concept.merged_with.uri,
                         "http://www.digitalhps.org/concepts/CONnN9sURrONpUs")
        self.assertEqual(concept.merged_with.concept_state, Concept.RESOLVED)

        created = manager.get(concept.merged_with.uri)
        self.assertIn(concept.uri, created.equal_to)

    def tearDown(self):
        Concept.objects.all().delete()
        Type.objects.all().delete()
        reconnect_signal(post_save, concept_post_save_receiver, Type)
