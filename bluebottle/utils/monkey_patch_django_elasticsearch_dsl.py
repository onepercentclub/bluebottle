from django.db import connection

import elasticsearch_dsl.document


class TenantAwareDocTypeOptions(elasticsearch_dsl.document.DocTypeOptions):
    @property
    def index(self):
        if self._index:
            return '{}-{}'.format(connection.tenant.schema_name, self._index)
        else:
            return None

    @index.setter
    def index(self, value):
        if value and value.startswith(connection.tenant.schema_name):
            value = value.replace(connection.tenant.schema_name + '-', '')

        self._index = value


elasticsearch_dsl.document.DocTypeOptions = TenantAwareDocTypeOptions
