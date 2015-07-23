from django.test import TestCase
from django.db.models.signals import post_save
from concepts.authorities import resolve, search
from concepts.models import Concept, Type
from concepts.signals import concept_post_save_receiver, type_post_save_receiver


def disconnect_signal(signal, receiver, sender):
    disconnect = getattr(signal, 'disconnect')
    disconnect(receiver, sender)


def reconnect_signal(signal, receiver, sender):
    connect = getattr(signal, 'connect')
    connect(receiver, sender=sender)

class TestConceptSearch(TestCase):
    def test_search(self):
        concepts = search('Bradshaw', pos='noun')
        self.assertIsInstance(concepts, list)
        self.assertIsInstance(concepts[0], Concept)

class TestConceptResolve(TestCase):
	def setUp(self):
		disconnect_signal(post_save, concept_post_save_receiver, Concept)
		disconnect_signal(post_save, type_post_save_receiver, Type)

	def test_resolve(self):
		c = Concept(uri="http://www.digitalhps.org/concepts/CONe5b55803-1ef6-4abe-b81c-1493e97421df",
					authority="ConceptpowerAuthority")
		c.save()
		resolve(Concept, c)
		resolve(Type, c.typed)

		self.assertTrue(hasattr(c, 'typed'))
		self.assertFalse(c.typed is None)
		self.assertTrue(c.resolved)
		self.assertTrue(c.typed.resolved)
		self.assertEqual(c.pos, 'noun')

	def tearDown(self):
		reconnect_signal(post_save, concept_post_save_receiver, Concept)
		reconnect_signal(post_save, type_post_save_receiver, Type)
