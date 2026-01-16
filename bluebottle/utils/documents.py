import os
import re
from django.conf import settings
from django.db import connection

from django_elasticsearch_dsl import Index, fields
from elasticsearch_dsl import analyzer

default_analyzer = analyzer(
    'standard',
    tokenizer="standard",
    filter=["lowercase", "asciifolding"],
)


class TextField(fields.TextField):
    def __init__(self, *args, **kwargs):
        kwargs['analyzer'] = default_analyzer

        super().__init__(*args, **kwargs)


class MultiTenantIndex(Index):

    @property
    def _name(self):
        if connection.tenant.schema_name != 'public':
            name = '{}-{}'.format(connection.tenant.schema_name, self.__name)
            test_prefix = getattr(settings, 'ELASTICSEARCH_TEST_INDEX_PREFIX', None)
            if test_prefix:
                process_id = os.getpid()
                name = '{}-pid{}-{}'.format(test_prefix, process_id, name)
            name = name.replace('_ded_test', '')
            return name

        return self.__name

    @_name.setter
    def _name(self, value):
        if value and value.startswith(connection.tenant.schema_name):
            value = value.replace(connection.tenant.schema_name + '-', '')
            test_prefix = getattr(settings, 'ELASTICSEARCH_TEST_INDEX_PREFIX', None)
            if test_prefix:
                value = re.sub(r'{}-pid\d+-'.format(re.escape(test_prefix)), '', value)
                value = value.replace(test_prefix + '-', '')
                value = value.replace('_ded_test', '')
        self.__name = value
