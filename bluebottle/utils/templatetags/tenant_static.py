from django import template
from django.templatetags.static import StaticNode
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db import connection
from django.utils._os import safe_join
import os


register = template.Library()


class StaticFilesNode(StaticNode):

    def url(self, context):
        context
        path = self.path.resolve(context)
        if not connection.tenant:
            return staticfiles_storage.url(path)

        local_path = safe_join(connection.tenant.client_name, path)
        if os.path.isfile(local_path):
            path = "/".join([connection.tenant.client_name, path])
        return staticfiles_storage.url(path)


@register.tag('tenant_static')
def do_static(parser, token):
    """
    A template tag that returns the URL to a file
    using staticfiles' storage backend

    Usage::

        {% static path [as varname] %}

    Examples::
        {% tenant_static "css/screen.css" %}
        Will resolve to /static/assets/<client_name>/css/screen.css
        <client_name> will depend on the Tenant

    """
    return StaticFilesNode.handle_token(parser, token)

