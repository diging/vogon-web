from django.conf import settings

from restable import RESTManager
# from goat.authorities.util import *

import json


class ConceptSearchResult(object):
    def __init__(self, name='', identifier='', **extra):
        assert isinstance(name, str)
        assert isinstance(identifier, str)
        self.name = name
        self.identifier = identifier
        self.extra = extra

    @property
    def local_identifier(self):
        return self.extra.get('local_identifier', None)

    @property
    def identities(self):
        return self.extra.get('identities', None)

    @property
    def description(self):
        return self.extra.get('description', None)

    @property
    def concept_type(self):
        return self.extra.get('concept_type', None)

    @property
    def raw(self):
        return self.extra.get('raw', None)


def _get_method_params(cfg):
    return [prm.get('accept') for prm
            in cfg.get('response', {}).get('parameters', {})]


class AuthorityManager(RESTManager):
    """
    Configuration-driven manager for authority services.
    """

    def get(self, identifier=None, local_identifier=None):
        """
        Get a concept record from the configured authority.

        Although both ``identifier`` and ``local_identifier`` are declared as
        optional, it is a good idea to pass them both and let the configuration
        sort things out.

        Parameters
        ----------
        identifier : str
            Used to populate the ``id`` parameter in the request.
        local_identifier : str
            Used to populate the ``local_id`` parameter in the request.

        Returns
        -------
        dict
        """
        _call = self._generic('get')
        if identifier and 'id' in _call.parameters:
            return _call(id=identifier)
        elif local_identifier and 'local_id' in _call.parameters:
            return _call(local_id=local_identifier)

    def search(self, params):
        """
        Search for concept records in the configured authority.

        Parameters
        ----------
        params : kwargs
            Query parameters used to populate the search request.

        Returns
        -------
        list
        """
        return [ConceptSearchResult(**o) for o in self._generic('search')(**params)]
