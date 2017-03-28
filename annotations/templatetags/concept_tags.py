from django import template
register = template.Library()


@register.filter(name='get_namespace')
def get_namespace(concept):
    from concepts.authorities import get_namespace as _get_namespace
    return _get_namespace(concept.uri)


@register.filter(name='is_conceptpower_namespaced')
def is_conceptpower_namespaced(concept):
    from concepts.authorities import ConceptpowerAuthority
    return get_namespace(concept) == ConceptpowerAuthority.namespace
