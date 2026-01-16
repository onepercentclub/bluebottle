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
            test_prefix = settings.ELASTICSEARCH_TEST_INDEX_PREFIX
            name = '{}-{}'.format(connection.tenant.schema_name, self.__name)
            if test_prefix:
                name = '{}-{}'.format(test_prefix, name)

            name.replace('_ded_test', '_dt')
            return name

        return self.__name

    @_name.setter
    def _name(self, value):

        if value and value.startswith(connection.tenant.schema_name):
            value = value.replace(connection.tenant.schema_name + '-', '')
            test_prefix = settings.ELASTICSEARCH_TEST_INDEX_PREFIX
            if test_prefix:
                value = value.replace(test_prefix + '-', '')
        value.replace('_ded_test', '_dt')
        self.__name = value
