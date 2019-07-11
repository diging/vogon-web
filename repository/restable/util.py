"""
Helper functions for parsing REST responses.
"""

import re, requests, json, jsonpickle
import lxml.etree as ET
from pprint import pprint


class ResultList(list):
    def __init__(self, *args, **kwargs):
        super(ResultList, self).__init__(*args)
        self.previous_page = kwargs.get('previous_page')
        self.next_page = kwargs.get('next_page')


class JSONData(dict):
    def __init__(self, obj={}):
        for key, value in obj.items():
            if type(value) is list:
                value = JSONArray(value)
            elif type(value) is dict:
                value = JSONData(value)
            self[key] = value

    def get(self, key, *args, **kwargs):
        return super(JSONData, self).get(key)


class JSONArray(list):
    """
    Adds ``get`` support to a list.
    """
    def __init__(self, obj=[]):
        for item in obj:
            if type(item) is dict:
                item = JSONData(item)
            self.append(item)

    def get(self, key, *args, **kwargs):
        """
        Return the value of ``key`` in the first object in list.
        """
        return self[0].get(key) if len(self) > 0 else None

    def get_list(self, key=None, *args, **kwargs):
        """
        Return the value of ``key`` in each object in list.
        """
        if key:
            return [obj.get(key) for obj in self if key in obj]
        return [obj for obj in self]


def is_multiple(tag):
    """
    Detect the multi-value flag (``*``) in a path part (``tag``).

    Parameters
    ----------
    tag : str

    Returns
    -------
    tuple
        tag name (str), multiple (bool)
    """
    if not tag:
        return None, None
    if tag == '*':
        return None, '*'
    return re.match(r'([^\*]+)(\*)?', tag).groups()


def get_recursive_pathfinder(nsmap={}, method='find', mult_method='findall'):
    """
    Generate a recursive function that follows the path in ``tags``, starting
    at ``elem``.
    """

    def _get(elem, tags):
        """
        Parameters
        ----------
        elem : :class:`lxml.etree.Element`
        tags : list
        """
        if not tags:    # Bottomed out; recursion stops.
            return elem

        this_tag, multiple = is_multiple(tags.pop())
        base = _get(elem, tags)

        if not base:
            return [] if multiple else None

        if type(base) is list:
            _apply = lambda b, t, meth: [getattr(c, meth)(t, nsmap) for c in b]
        else:
            _apply = lambda b, t, meth: getattr(b, meth)(t, nsmap)


        if multiple:
            return _apply(base, this_tag, mult_method)
        return _apply(base, this_tag, method)
    return _get


def _to_unicode(e):
    if isinstance(e, unicode):
        return e
    return e.decode('utf-8')


_etree_attribute_getter = lambda e, attr: _to_unicode(getattr(e, 'attrib', {}).get(attr, u'').strip())#.encode('utf-8')
_etree_cdata_getter = lambda e: _to_unicode(getattr(getattr(e, 'text', u''), 'strip', lambda: u'')())#.encode('utf-8')
_json_content_getter = lambda e: e


def content_picker_factory(env, content_getter=_etree_cdata_getter, attrib_getter=_etree_attribute_getter):
    """
    Generates a function that retrives the CDATA content or attribute value of
    an element.

    Parameters
    ----------
    env : dict

    Returns
    -------
    function
    """
    attribute, sep = env.get('attribute', False), env.get('sep', None)
    _separator = lambda value: [v.strip() for v in value.split(sep)] if sep else value
    if attribute:
        return lambda elem: _separator(attrib_getter(elem, attribute[1:-1]))
    return lambda elem: _separator(content_getter(elem))


def passthrough_picker_factory(env, *args, **kwargs):
    """
    Generates a function that simply returns a passed
    :class:`lxml.etree.Element`\.

    Parameters
    ----------
    env : dict

    Returns
    -------
    function
    """
    return lambda e: e


def decompose_path(path_string):
    """
    Split a path string into its constituent parts.

    Parameters
    ----------
    path_string : str

    Returns
    -------
    path : list
    attribute : str or None
    """
    if '|' in path_string:
        try:
            path_string, sep = path_string.split('|')
        except ValueError:
            raise ValueError("Malformed path: only one separator reference"
                             " (|) allowed.")
    else:
        sep = None

    path, attribute = re.match(r'([^\[]+)(\[.+\])?', path_string).groups()
    if '[' in path and not attribute:
        raise ValueError("Malformed path: attribute references must come at"
                         " the very end of the path.")

    path = path.split('/')
    return path, attribute, sep


def _parse_path(path_string, nsmap={}, picker_factory={},
                content_getter=_etree_cdata_getter,
                attrib_getter=_etree_attribute_getter,
                get_method='find', mult_method='findall'):
    """
    Generate a function that will retrieve data of interest from an arbitrary
    object. This combines common logic from public parser functions.

    Parameters
    ----------
    path_string : str
        See docs for how this should be written. TODO: write the docs.
    nsmap: dict
    picker_factory : function
    get_method : str
    list_method : str

    Returns
    -------
    function
    """
    path, attribute, sep = decompose_path(path_string)
    _get = get_recursive_pathfinder(nsmap=nsmap, method=get_method,
                                    mult_method=mult_method)
    _picker = picker_factory(locals(), content_getter=content_getter)

    def _apply(obj):    # No empty values.
        value = _picker(obj)
        if value and (not type(value) is list or value[0]):
            return value

    def _call(elem):
        base = _get(elem, path)
        if type(base) is list:
            return [_apply(child) for child in base]
        return _apply(base)
    return _call


def parse_json_path(path_string, nsmap={}, picker_factory=content_picker_factory):
    """
    Generate a function that will retrieve data of interest from a
    :class:`.JSONData` object.

    Parameters
    ----------
    path_string : str
        See docs for how this should be written. TODO: write the docs.
    nsmap: dict
        Not used.
    picker_factory : function


    Returns
    -------
    function
    """
    return _parse_path(path_string, nsmap, picker_factory, _json_content_getter,
                       _json_content_getter, 'get', 'get_list')


def parse_xml_path(path_string, nsmap={}, picker_factory=content_picker_factory):
    """
    Generate a function that will retrieve data of interest from an
    :class:`lxml.etree.Element`\.

    Parameters
    ----------
    path_string : str
        See docs for how this should be written. TODO: write the docs.
    nsmap: dict
        See the ``lxml.etree`` docs.
    picker_factory : function


    Returns
    -------
    function
    """
    return _parse_path(path_string, nsmap, picker_factory)


def generate_request(config, glob={}):
    """
    Generate a function that performs an HTTP request based on the configuration
    in ``config``.

    Parameters
    ----------
    config : dict
    glob : dict

    Returns
    -------
    function
        Expects keyword arguments defined in the configuration. If provided,
        ``headers`` will be pulled out and passed as headers in the request.
    """
    try:
        path_partial = config['path']
    except KeyError:
        raise ValueError("Malformed configuration: no path specified.")

    method = config.get("method", "GET")    # GET by default.

    # Maps accept -> send parameter names.
    parameters = {param['accept']: param['send']
                  for param in config.get("parameters", [])}
    required = {param['accept'] for param in config.get("parameters", [])
                if param.get('required', False)}
    defaults = {param['accept']: param['default']
                for param in config.get("parameters", [])
                if 'default' in param}

    format_keys = re.findall(r'\{([^\}]+)\}', path_partial)
    fmt = {k: v for k, v in glob.items() if k in format_keys}

    def _get_path(extra={}):
        fmt.update(extra)
        return path_partial.format(**fmt)

    def _call(**params):
        """
        Perform the configured request.

        Parameters
        ----------
        params : kwargs

        Returns
        -------

        """
        headers = params.pop('headers', {})
        for param in required:
            if param not in params:
                raise TypeError('expected parameter %s' % param)

        # Relabel accepts -> send parameter names.
        params = {parameters.get(k): v for k, v in params.items()
                  if k in parameters}

        extra = {key: params.pop(key, defaults.pop(key, ''))
                 for key in format_keys
                 if key not in fmt}    # Don't overwrite.

        if method == 'GET':
            request_method = requests.get
            payload = {'params': params, 'headers': headers}
        elif method == 'POST':
            request_method = requests.post
            payload = {'data': params, 'headers': headers}

        target = _get_path(extra)
        try:
            response = request_method(target, **payload)
        except Exception as E:
            print('request to %s failed with %s' % (target, str(payload)))
            raise E
        if response.status_code >= 400:
            print('request to %s failed' % response.url)
            raise IOError(response.content)
        return response.content
    return _call


def generate_simple_request(path, method):
    def _call(**params):
        """
        Perform the configured request.

        Parameters
        ----------
        params : kwargs

        Returns
        -------

        """
        headers = params.pop('headers', {})

        if method == 'GET':
            request_method = requests.get
            payload = {'params': params, 'headers': headers}
        elif method == 'POST':
            request_method = requests.post
            payload = {'data': params, 'headers': headers}
        response = request_method(path, **params)
        if response.status_code >= 400:
            raise IOError(response.content)
        return response.content
    return _call


def parse_result(config, data, path_parser=parse_xml_path, glob={}, nsmap={}):
    """
    Extract data from an :class:`lxml.etree.Element` using a configuration
    schema.

    Parameters
    ----------
    config : dict
    data : :class:`lxml.etree.Element`
    path_parser : function
    glob : dict
    nsmap : dict

    Returns
    -------
    list
    """
    base_path = config.get('path', None)
    _, multiple = is_multiple(base_path)
    if base_path:
        _parser = path_parser(base_path, nsmap=nsmap,
                              picker_factory=passthrough_picker_factory)
        base_elems = _parser(data)
    else:
        base_elems = [data]

    data = ResultList()

    # Pagination.
    pagination = config.get('pagination')
    if pagination:
        if "next" in pagination:
            data.next_page = generate_simple_request(path_parser(pagination.get("next").get('path'), nsmap)(data), 'GET')
        if "previous" in pagination:
            data.previous_page = generate_simple_request(path_parser(pagination.get("previous").get('path'), nsmap)(data), 'GET')

    base_elems = [base_elems] if not type(base_elems) is list else base_elems
    for base_elem in base_elems:
        # Serialized raw data is preserved.
        parsed_data = {'raw': jsonpickle.dumps(base_elem)}

        # Each parameter is parsed separately.
        for parameter in config.get('parameters'):
            name = parameter.get('name')
            ctype = parameter.get('type')

            value = path_parser(parameter.get('path'), nsmap)(base_elem)
            if ctype == 'object':
                value = parse_result(parameter.get('config'), value,
                                     path_parser=path_parser, glob=glob,
                                     nsmap=nsmap)

            # Templated parameters use response data and globals to generate
            #  values (e.g. URI from ID).
            template = parameter.get('template')
            if template:
                # Isolate only the globals needed to render the template.
                format_keys = re.findall(r'\{([^\}]+)\}', template)
                fmt = {k: v for k, v in glob.items() if k in format_keys}
                if name in format_keys:    # Probably this is always true...
                    fmt[name] = value
                value = template.format(**fmt)
            parsed_data[name] = value
        data.append(parsed_data)

    if not multiple:
        assert len(data) == 1
        return data[0]
    return data


# This isn't particularly special at the moment, but makes it easier to swap
#  out parsers later, or add additional logic.
def parse_raw_xml(raw):
    """
    Parse raw XML response content.

    Parameters
    ----------
    raw : unicode

    Returns
    -------
    :class:`lxml.etree.Element`
    """
    # if type(raw) is str:
    #     raw = raw.decode('utf-8')
    return ET.fromstring(raw)


def parse_raw_json(raw):
    """
    Parse raw JSON response content.

    Parameters
    ----------
    raw : unicode

    Returns
    -------
    :class:`lxml.etree.Element`
    """
    if type(raw) is str:
        raw = raw.decode('utf-8')
    return JSONData(json.loads(raw))
