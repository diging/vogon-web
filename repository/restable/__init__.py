from .util import *

import json


def _get_method_params(cfg):
    return [prm.get('accept') for prm
            in cfg.get('response', {}).get('parameters', {})]


class RESTManager(object):
    """
    Configuration-driven manager for REST services.

    Parameters
    ----------
    config : str
        A REST configuration (must be valid JSON).
    """

    def __init__(self, configuration, **params):
        self.configuration = json.loads(configuration)
        self.methods = {method.pop('name'):method for method
                        in self.configuration.get("methods")}
        self.params = params

    def _get_globs(self):
        return {'endpoint': self.configuration.get('endpoint', '')}

    def _get_nsmap(self, config):
        return {
            ns['prefix']: ns['namespace']
            for ns in config.get('response', {}).get('namespaces', [])
        }

    def _get_method_config(self, name):
        if name not in self.methods:
            raise NotImplementedError('%s not defined in configuration' % name)
        return self.methods.get(name)

    def _generic(self, name):
        """
        Build a method using the configuration identified by ``name``.

        Parameters
        ----------
        name : str
            Must be the name of a method defined in the configuration.

        Returns
        -------
        function
        """
        config = self._get_method_config(name)
        response_type = config.get('response', {}).get('type', 'xml').lower()

        if response_type not in ['xml', 'json']:
            raise NotImplementedError('No parser for %s' % response_type)

        if response_type == 'xml':
            parse_raw = parse_raw_xml
            parse_path = parse_xml_path
        elif response_type == 'json':
            parse_raw = parse_raw_json
            parse_path = parse_json_path

        request_func = generate_request(config, self._get_globs())

        def _call(*args, **kwargs):
            params = self.params
            params.update(kwargs)
            return parse_result(config.get('response'),
                                parse_raw(request_func(*args, **params)),
                                parse_path,
                                self._get_globs(),
                                self._get_nsmap(config))
        _call.parameters = _get_method_params(config)
        return _call

    def __getattr__(self, name):
        if name in self.methods:
            return self._generic(name)
        return super(AuthorityManager, self).__getattr__(name)

    def accepts(self, method, *params):
        config = self._get_method_config(method)
        accepted = {p.get('accept', '') for p in config.get('parameters', [])}
        return all([param in accepted for param in params])

    def parse(self, method, data):
        """
        Parse raw data as a response for ``method``.

        Parameters
        ----------
        method : str
            Name of a method defined in this :class:`.RestManager`\'s
            configuration.
        data : str
            Raw data (e.g. JSON or XML).

        Returns
        -------
        dict
        """
        config = self._get_method_config(method)
        response_type = config.get('response', {}).get('type', 'xml').lower()

        if response_type not in ['xml', 'json']:
            raise NotImplementedError('No parser for %s' % response_type)

        if response_type == 'xml':
            parse_raw = parse_raw_xml
            parse_path = parse_xml_path
        elif response_type == 'json':
            parse_raw = parse_raw_json
            parse_path = parse_json_path
            return parse_result(config.get('response'), parse_raw(data),
                                parse_path, self._get_globs(),
                                self._get_nsmap(config))
