from functools import wraps

from django.db import connection
from memoize import memoize as original_memoize


def get_tenant_cache_name(function_name):
    try:
        tenant_name = connection.tenant.schema_name
    except AttributeError:
        tenant_name = 'public'
    return f'{function_name}_{tenant_name}'


def memoize(timeout=3600, make_name=None):
    def tenant_aware_make_name(fname):
        if make_name is not None:
            fname = make_name(fname)
        return get_tenant_cache_name(fname)

    memoizer = original_memoize(timeout=timeout, make_name=tenant_aware_make_name)

    def decorator(function):
        memoized = memoizer(function)

        @wraps(function)
        def wrapper(*args, **kwargs):
            from bluebottle.clients.utils import LocalTenant

            tenant = getattr(connection, 'tenant', None)
            with LocalTenant(tenant):
                return memoized(*args, **kwargs)

        wrapper.uncached = memoized.uncached
        wrapper.cache_timeout = memoized.cache_timeout
        wrapper.make_cache_key = memoized.make_cache_key
        wrapper.delete_memoized = memoized.delete_memoized
        return wrapper

    return decorator
