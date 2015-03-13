import hashlib

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import connection
from django.template.base import TemplateDoesNotExist
from django.template.loader import BaseLoader
from django.utils._os import safe_join


class FilesystemLoader(BaseLoader):
    """
    Based on FileSystemLoader from django-tenant-schemas:
    https://github.com/bernardopires/django-tenant-schemas/blob/master/tenant_schemas/template_loaders.py#L79
    Changes are:
    - Use MULTI_TENANT_DIR from config for path (not multiple paths in MULTITENANT_TEMPLATE_DIRS)
    - Use tenant.client_name not tenant.domain_url
    """

    is_usable = True

    def get_template_sources(self, template_name, template_dirs=None):
        if not connection.tenant:
            return
        if not template_dirs:
            try:
                template_dirs = [settings.MULTI_TENANT_DIR]
            except AttributeError:
                raise ImproperlyConfigured('To use %s.%s you must define the MULTI_TENANT_DIR' %
                                           (__name__, FilesystemLoader.__name__))
        for template_dir in template_dirs:
            try:
                if '%s' in template_dir:
                    yield safe_join(template_dir % connection.tenant.client_name, 'templates', template_name)
                else:
                    yield safe_join(template_dir, connection.tenant.client_name, 'templates', template_name)
            except UnicodeDecodeError:
                # The template dir name was a bytestring that wasn't valid UTF-8.
                raise
            except ValueError:
                # The joined path was located outside of this particular
                # template_dir (it might be inside another one, so this isn't
                # fatal).
                pass

    def load_template_source(self, template_name, template_dirs=None):
        tried = []
        for filepath in self.get_template_sources(template_name, template_dirs):
            try:
                with open(filepath, 'rb') as fp:
                    return (fp.read().decode(settings.FILE_CHARSET), filepath)
            except IOError:
                tried.append(filepath)
        if tried:
            error_msg = "Tried %s" % tried
        else:
            error_msg = "Your TEMPLATE_DIRS setting is empty. Change it to point to at least one template directory."
        raise TemplateDoesNotExist(error_msg)
    load_template_source.is_usable = True
