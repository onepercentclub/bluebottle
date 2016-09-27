import re

from django.utils import timezone
from django.conf import settings
from django.utils.translation import ugettext as _
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import connection

from .tasks import queue_analytics_record


@receiver(post_save, weak=False, dispatch_uid='model_analytics')
def post_save_analytics(sender, instance, **kwargs):
    if not getattr(settings, 'ANALYTICS_ENABLED', False):
        return

    # Return early if instance is a migration.
    if instance.__class__.__name__ == 'Migration':
        return

    created = kwargs['created']

    # Check if the instance has an _original_status and whether the status
    # has changed. If not then skip recording this save event. This can be
    # skipped if the record has been created as we will always record metrics
    # for a newly created record.
    try:
        if not created and instance._original_status == instance.status:
            return
    except AttributeError:
        pass

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

    def snakecase(name):
        return re.sub("([A-Z])", "_\\1", name).lower().lstrip("_")

    try:
        analytics_cls = instance.Analytics
        tenant_name = connection.schema_name
    except AttributeError:
        return

    analytics = analytics_cls()
    try:
        if analytics.skip(instance, created):
            return
    except AttributeError:
        pass
    
    # Check for instance specific tags
    try:
        tags = analytics.extra_tags(instance, created)
    except AttributeError:
        tags = {}

    fields = {}
    tags['type'] = getattr(analytics, 'type', snakecase(instance.__class__.__name__))
    tags['tenant'] = tenant_name

    # Process tags
    try:
        for label, tag_attr in analytics.tags.iteritems():
            attr = multi_getattr(instance, tag_attr, default='')
            # If attr is a string then try to translate
            # Note: tag values should always be strings.
            if isinstance(attr, basestring):
                attr = _(attr)
            tags[label] = attr
    except AttributeError:
        pass

    # Process fields
    try:
        for label, field_attr in analytics.fields.iteritems():
            attr = multi_getattr(instance, field_attr, default='')
            # If attr is a string then try to translate
            if isinstance(attr, basestring):
                attr = _(attr)
            fields[label] = attr
    except AttributeError:
        pass

    # If enabled, use celery to queue task
    if not getattr(settings, 'CELERY_RESULT_BACKEND', None):
        queue_analytics_record(timestamp=timezone.now(),
                               tags=tags, fields=fields)
    else:
        queue_analytics_record.delay(timestamp=timezone.now(),
                                     tags=tags, fields=fields)
