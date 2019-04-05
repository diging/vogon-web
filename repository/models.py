from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import SafeText

import json, datetime, requests, copy, xmltodict
from urllib.parse import urljoin
from string import Formatter
from uuid import uuid4

from repository import auth


class FieldValue(object):
    def __init__(self, name, value, value_type):
        self.name = name
        self.value = value
        self.value_type = value_type
        self.render_value = getattr(self, '_render_%s' % value_type)

    def _render_bool(self):
        if self.value:
            return SafeText('<span class="glyphicon glyphicon-ok"></span>')
        return SafeText('<span class="glyphicon glyphicon-remove"></span>')

    def _render_text(self):
        return self.value

    def _render_int(self):
        return self.value

    def _render_float(self):
        return self.value

    def _render_url(self):
        return SafeText('<span class="text-warning">%s</span>' % self.value)

    def _render_datetime(self):
        # TODO: this should actually implement datetime formatting.
        return self.value

    def render(self):
        return SafeText('<dt>%s</dt><dd>%s</dd>' % (self.name, self.render_value()))

    def __str__(self):
        return self.render()

    def __unicode__(self):
        return self.render()


class ContentObject(object):
    def __init__(self, data):
        self.id = data.pop('id').value
        self.data = data


class ContentContainer(object):
    def __init__(self, content_data):
        self.contents = {}
        for datum in content_data:
            datum = ContentObject(datum)
            self.contents[int(datum.id)] = datum

    def get(self, key):
        return self.contents.get(key, None)

    def items(self):
        return list(self.contents.items())

    @property
    def count(self):
        return len(self.contents)


class SeriesContainer(ContentContainer):
    pass


class Result(object):
    def __init__(self, **kwargs):
        content = kwargs.pop('content', None)
        self.data = kwargs
        for field, value in list(self.data.items()):
            setattr(self, field, value)

        if content:
            if type(content) is not list:
                content = [content]

            self.content = ContentContainer(content)

    def iteritems(self):
        return iter(list(self.data.items()))

    def get(self, key, default=None):
        return self.data.get(key, default)


class ResultSet(object):
    def __init__(self, results, **kwargs):
        for key, value in list(kwargs.items()):
            setattr(self, key, value)
        self.results = results

    @property
    def count(self):
        """
        The number of :class:`.Result`\s in this :class:`.ResultSet`\.
        """
        return len(self.results)

    def __getitem__(self, key):
        if type(key) is int:
            return self.results[key]
        return getattr(self, key, None)


class Repository(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    configuration = models.TextField()

    # def __init__(self, *args, **kwargs):
    #     super(Repository, self).__init__(*args, **kwargs)
    #
    #     try:
    #         for method in self.configured_methods:
    #             print '!', method
    #             setattr(self, method, self._method_factory(method))
    #     except ValueError:
    #         pass

    def manager(self, user):
        from repository.managers import RepositoryManager
        return RepositoryManager(self.configuration, user=user)

    def can(self, method_name):
        return method_name in list(self._get_configuration()['methods'].keys())

    def __getattr__(self, key):
        if key.startswith('can_'):
            return self.can(key[4:])
        return getattr(super(Repository, self), key)

    @property
    def endpoint(self):
        return self._get_configuration()['endpoint']

    @property
    def configured_methods(self):
        return list(self._get_configuration()['methods'].keys())

    @staticmethod
    def _list_handler(results):
        return ResultSet([Result(**result) for result in results])

    @staticmethod
    def _instance_handler(result):
        return Result(**result)

    def _get_configuration(self, method=None):
        config = json.loads(self.configuration)
        if method:
            try:
                return config['methods'][method]
            except KeyError:
                raise AttributeError('No such method for this repository')

        return config

    def _method_factory(self, method):
        return lambda **q: self._execute_method(method, **q)

    def _get_request_fields(self, method):
        return self._get_configuration(method)['request'].get('fields', {})

    def _get_response_fields(self, method):
        return self._get_configuration(method)['response'].get('fields', {})

    def _validate_field_value(self, field, value):
        if 'type' not in field:
            return True
        try:
            if field['type'] == 'text':
                assert type(value) in [str, str]
            elif field['type'] == 'bool':
                assert type(value) is bool
            elif field['type'] == 'date':
                assert type(value) is datetime.datetime
            elif field['type'] == 'int':
                assert type(value) is int
            elif field['type'] == 'float':
                assert type(value) is float
        except AssertionError:
            raise ValueError('Invalid value for field %s: not a %s' % \
                             (field['name'], field['type']))

    def _render_path_template(self, method, template, **payload):
        config = self._get_configuration(method)
        field_part = template.format(**payload)
        return urljoin(config['path'], field_part)

    def _get_path_for_method(self, method, **kwargs):
        config = self._get_configuration(method)
        template = config['request'].get('template', None)
        if template:
            path = self._render_path_template(method, template, **kwargs)
        else:
            path = config['path']
        return urljoin(self.endpoint, path)

    # def _get_pagination(self, method, data):
    #     config = self._get_configuration(method)
    #     pagination_config = config['results'].get('pagination', None)
    #     if pagination_config and pagination_config.get('paginated', False):

    def _get_data_by_path(self, data, path):
        path_parts = path.split('.')
        data = copy.copy(data)

        # Paths can be arbitrarily deep.
        if len(path_parts) > 0 and path_parts[0]:
            for part in path_parts:
                try:
                    data = data.get(part)
                except (KeyError, AttributeError):
                    # TODO: make this more informative, or add logging.
                    raise RuntimeError('Response data does not match configuration')
        # If there is no usable path information, we simply return the data.
        return data

    def _get_field_data(self, fields, response_type, data):
        # The `path` of each field specifies where in the data to find data for
        #  that field.

        field_map = {f.get('path'): k for k, f in list(fields.items()) if 'path' in f}
        config = self._get_configuration()

        def map_data(result):
            mapped_data = {}
            for path, field in list(field_map.items()):
                mapped_data[fields[field]['name']] = FieldValue(
                    fields[field]['display'],
                    self._get_data_by_path(result, path),
                    fields[field]['type']
                )

            # Rather than reading a field value directly from data, the value
            #  may be a composite of values from other fields, or the
            #  repository configuration itself. Composite fields are described
            #  using the 'template' parameter in the field description.
            for field in list(fields.values()):
                if 'template' in field:
                    template = field['template']
                    template_keys = [o[1] for o in Formatter().parse(template)]
                    template_values = {}
                    for key in template_keys:
                        if key in mapped_data:
                            template_values[key] = mapped_data[key].value
                        elif key in data:
                            template_values[key] = data[key]
                        elif key in config:
                            template_values[key] = config[key]

                    mapped_data[field['name']] = FieldValue(
                        field['display'],
                        template.format(**template_values),
                        'text'
                    )

            return mapped_data
        if not data:
            return []
        if response_type == 'list':
            data = [map_data(result) for result in data]
        elif response_type == 'instance':
            data = map_data(data)
        return data

    def _get_content_data(self, method, data, response_type='instance'):

        config = self._get_configuration(method)['response']
        if 'content' not in config:
            return

        # If metadata about the content of a result is present in the result
        #  data itself, then this is indicated with the 'path' paramter.
        content_path = config['content'].get('path', None)
        content_method = config['content'].get('method', None)
        if method and not content_path:
            external_data = self._execute_method(content_method, raw=True, **data)
            return external_data

        content_data = self._get_data_by_path(data, content_path)
        content_fields = config['content']['fields']
        content_results_type = config['content'].get('results', 'instance')
        if response_type == 'instance':
            return self._get_field_data(content_fields, content_results_type, content_data)
        elif response_type == 'list':
            return [self._get_field_data(content_fields, content_results_type, datum) for datum in data]

        return None

    def _get_results(self, method, data):
        # TODO: this should be more sophisticated.
        if type(data) is list:
            return data

        config = self._get_configuration(method)['response']

        # The response path points to a property in the data that represents the
        #  result set.
        data = self._get_data_by_path(data, config.get('path', ''))

        # These are the fields that we expect to find.
        fields = self._get_response_fields(method)
        response_type = config.get('results', 'instance')

        if response_type == 'list' and not type(data) is list:
            data = [data]

        content = self._get_content_data(method, data, response_type)
        data = self._get_field_data(fields, response_type, data)
        if response_type == 'instance' and content:
            data['content'] = content
        elif response_type == 'list' and content:
            for datum, ct in zip(data, content):
                datum['content'] = ct

        return data

    def _get_response_handler(self, method):
        response_type = self._get_configuration(method)['response']['results']
        if response_type == 'list':
            return self._list_handler
        elif response_type == 'instance':
            return self._instance_handler

    def _execute_method(self, method, **kwargs):
        """
        Handle a method call for this :class:`.Repository`\.

        This method is returned whenever a configured method is requested.

        Parameters
        ----------
        method : str
            Name of a method in the ``.configuration`` for this repository.
        kwargs : kwargs
            Query/request parameters for the method.

        Returns
        -------
        :class:`.Result` or :class:`.ResultSet`
        """

        # If raw is True, then the raw result data will be returned, rather
        # than wrapping the results as Result and ResultSet instances.
        raw = kwargs.pop('raw', False)
        user = kwargs.pop('user', None)

        fields = self._get_request_fields(method)
        config = self._get_configuration()

        payload = {}
        for key, value in list(kwargs.items()):
            if key not in fields:
                continue
            self._validate_field_value(fields[key], value)
            payload[key] = value

        request_path = self._get_path_for_method(method, **kwargs)
        request_args = {
             'params': payload,
             'headers': {},
        }
        if config['format'] == 'xml':
            request_args['headers'].update({'Accept': 'application/xml'})

        auth_method_name = config.get('auth')

        if auth_method_name and user:
            auth_method = getattr(auth, auth_method_name, None)
            if auth_method:
                request_args['headers'].update(auth_method(user))

        response = requests.get(request_path, **request_args)

        if response.status_code != requests.codes.OK:
            raise IOError(response.content)
        if config['format'] == 'json':
            response_content = response.json()
        elif config['format'] == 'xml':
            response_content = xmltodict.parse(response.text)

        result_data = self._get_results(method, response_content)

        if raw:    # Just the facts.
            return result_data

        return self._get_response_handler(method)(result_data)
