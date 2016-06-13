from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import SafeText

import json, datetime, requests
import copy
from urlparse import urljoin


class FieldValue(object):
    def __init__(self, name, value, value_type):
        self.name = name
        self.value = value
        self.value_type = value_type
        self.render_value = getattr(self, '_render_%s' % value_type)

    def _render_bool(self):
        if self.value:
            return SafeText(u'<span class="glyphicon glyphicon-ok"></span>')
        return SafeText(u'<span class="glyphicon glyphicon-remove"></span>')

    def _render_text(self):
        return self.value

    def _render_int(self):
        return self.value

    def _render_float(self):
        return self.value

    def _render_url(self):
        return SafeText(u'<a href="%s">%s</a>' % (self.value, self.value))

    def render(self):
        return SafeText(u'<dt>%s</dt><dd>%s</dd>' % (self.name, self.render_value()))

    def __str__(self):
        return self.render()

    def __unicode__(self):
        return self.render()


class Result(object):
    def __init__(self, **kwargs):
        self.data = kwargs

        for key, value in kwargs.iteritems():
            setattr(self, key, value)

    def iteritems(self):
        return self.data.iteritems()

    def get(self, key, default=None):
        return self.data.get(key, default)


class ResultSet(object):
    def __init__(self, results, **kwargs):
        for key, value in kwargs.iteritems():
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

    def __init__(self, *args, **kwargs):
        super(Repository, self).__init__(*args, **kwargs)

        try:
            for method in self.configured_methods:
                setattr(self, method, self._method_factory(method))
        except ValueError:
            pass

    @property
    def endpoint(self):
        return self._get_configuration()['endpoint']

    @property
    def configured_methods(self):
        return self._get_configuration()['methods'].keys()

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
                assert type(value) in [str, unicode]
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



    def _get_results(self, method, data):
        config = self._get_configuration(method)
        results_path = config['response']['path'].split('.')

        if type(data) is list and not results_path[0]:
            return data

        # The results_path points to a property in the data that represents the
        #  result set.
        if results_path[0]:
            for key in results_path:
                data = data.get(key)

        fields = self._get_response_fields(method)
        field_map = {f['path']: k for k, f in fields.iteritems()}
        response_type = self._get_configuration(method)['response']['results']

        def map_data(result):
            mapped_data = {}
            for path, field in field_map.iteritems():
                if path in result:
                    mapped_data[fields[field]['name']] = FieldValue(fields[field]['display'], result[path], fields[field]['type'])
            return mapped_data


        if response_type == 'list':
            data = [map_data(result) for result in data]
        elif response_type == 'instance':
            data = map_data(data)
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

        fields = self._get_request_fields(method)

        payload = {}
        for key, value in kwargs.iteritems():
            if key not in fields:
                continue
            self._validate_field_value(fields[key], value)
            payload[key] = value

        request_path = self._get_path_for_method(method, **kwargs)
        response = requests.get(request_path, params=payload)


        result_data = self._get_results(method, response.json())

        response_handler = self._get_response_handler(method)
        return response_handler(result_data)
