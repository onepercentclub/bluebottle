from django.db import connection


def tenant(request):
    """
    Add tenant to request context
    """
    if connection.tenant:
        tenant = connection.tenant
        return {
            'TENANT': connection,
            'TENANT_LANGUAGE': '{0}{1}'.format(tenant.client_name,
                                               request.LANGUAGE_CODE)
        }
    return {}
