from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

class AnnotationsConfig(AppConfig):
    name = 'annotations'
    verbose_name = _('annotations')

    def ready(self):
        import annotations.signals
