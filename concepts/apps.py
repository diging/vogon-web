from django.apps import AppConfig

class ConceptsConfig(AppConfig):
    name = 'concepts'

    def ready(self):
        import concepts.signals
        super(ConceptsConfig, self).ready()