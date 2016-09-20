import re

from django.utils.translation import ugettext as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import connection

from .utils import queue_analytics_record


@receiver(post_save, weak=False, dispatch_uid='model_analytics')
def post_save_analytics(sender, instance, **kwargs):
    def multi_getattr(obj, attr, **kw):
        attributes = attr.split(".")
        for i in attributes:
            try:
                obj = getattr(obj, i)
                if callable(obj):
                    obj = obj()
            except AttributeError:
                if kw.has_key('default'):
                    return kw['default']
                else:
                    raise
        return obj

    def camelize(name):
        return re.sub('_.',lambda x: x.group()[1].upper(), name)

    try:
        analytics_cls = instance.Analytics
        tenant_name = connection.schema_name

        analytics = analytics_cls()
        tags = {}
        tags['type'] = getattr(analytics, 'type', camelize(instance.__class__.__name__))
        tags['tenant'] = tenant_name

        for label, tag_attr in analytics.tags.iteritems():
            attr = multi_getattr(instance, tag_attr, default='')
            # If attr is a string then try to translate
            # Note: tag values should always be strings.
            if isinstance(attr, basestring):
                attr = _(attr)
            tags[label] = attr

        queue_analytics_record(tags=tags)

    except AttributeError:
        pass
