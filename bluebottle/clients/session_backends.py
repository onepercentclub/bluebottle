from datetime import datetime, timedelta

from django.contrib.sessions.backends.db import SessionStore as DBSessionStore
from django.db import connection
from django.utils import timezone

from bluebottle.clients import properties

TENANT_SESSION_KEY = '_tenant'


def current_schema():
    tenant = getattr(connection, 'tenant', None)
    return getattr(tenant, 'schema_name', None)


class SessionStore(DBSessionStore):
    """
    Sessions are stored in the shared schema, so bind each one to the tenant
    that created it and ignore it on any other tenant.
    """

    def load(self):
        data = super().load()
        if data and data.get(TENANT_SESSION_KEY) != current_schema():
            self._session_key = None
            return {}
        return data

    def create_model_instance(self, data):
        return super().create_model_instance(
            {**data, TENANT_SESSION_KEY: current_schema()}
        )

    def get_expiry_age(self, **kwargs):
        """Get the number of seconds until the session expires.

        Optionally, this function accepts `modification` and `expiry` keyword
        arguments specifying the modification and expiry of the session.
        """
        try:
            modification = kwargs['modification']
        except KeyError:
            modification = timezone.now()
        # Make the difference between "expiry=None passed in kwargs" and
        # "expiry not passed in kwargs", in order to guarantee not to trigger
        # self.load() when expiry is provided.
        try:
            expiry = kwargs['expiry']
        except KeyError:
            expiry = self.get('_session_expiry')

        if not expiry:   # Checks both None and 0 cases
            return properties.SESSION_COOKIE_AGE
        if not isinstance(expiry, datetime):
            return expiry
        delta = expiry - modification
        return delta.days * 86400 + delta.seconds

    def get_expiry_date(self, **kwargs):
        """Get session the expiry date (as a datetime object).

        Optionally, this function accepts `modification` and `expiry` keyword
        arguments specifying the modification and expiry of the session.
        """
        try:
            modification = kwargs['modification']
        except KeyError:
            modification = timezone.now()
        # Same comment as in get_expiry_age
        try:
            expiry = kwargs['expiry']
        except KeyError:
            expiry = self.get('_session_expiry')

        if isinstance(expiry, datetime):
            return expiry
        if not expiry:   # Checks both None and 0 cases
            expiry = properties.SESSION_COOKIE_AGE
        return modification + timedelta(seconds=expiry)
