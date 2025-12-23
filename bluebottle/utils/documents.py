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
            return '{}-{}'.format(connection.tenant.schema_name, self.__name)
        return self.__name

    @_name.setter
    def _name(self, value):

        if value and value.startswith(connection.tenant.schema_name):
            value = value.replace(connection.tenant.schema_name + '-', '')

        self.__name = value
