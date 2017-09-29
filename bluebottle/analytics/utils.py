import re
import logging

from django.conf import settings
from django.db import connection
from django.utils import timezone
from django.utils.translation import ugettext as _
from tenant_extras.utils import TenantLanguage

from bluebottle.clients import properties
from bluebottle.clients.utils import LocalTenant
from .tasks import queue_analytics_record


logger = logging.getLogger(__name__)


def _multi_getattr(obj, attr, **kw):
    attributes = attr.split(".")
    for i in attributes:
        try:
            obj = getattr(obj, i)
            if callable(obj):
                obj = obj()
        except AttributeError:
            if 'default' in kw:
                return kw['default']
            else:
                raise
    return obj


def process(instance, created):
    instance_name = instance.__class__.__name__

    # _merge_attrs combines the base and instance tag or field values with
    # the class values. It also handles translateable attrs.
    def _merge_attrs(data, attrs):
        try:
            items = attrs.iteritems()
        except AttributeError:
            logger.exception('analytics_merge_attrs')
            return

        for label, attr in items:
            options = {}
            # If a dict is passed then the key is the dotted
            # property string and the value is options.
            try:
                new_attr = attr.keys()[0]
                options = attr[new_attr]
                attr = new_attr
            except AttributeError:
                # TODO: Logging
                pass

            value = _multi_getattr(instance, attr, default='')

            if options.get('translate', False):
                with LocalTenant():
                    # Translate using the default tenant language
                    with TenantLanguage(getattr(properties, 'LANGUAGE_CODE', 'en')):
                        # If attr is a string then try to translate
                        # Note: tag values should always be strings.
                        value = _(value)

            data[label] = value

    def snakecase(name):
        return re.sub("([A-Z])", "_\\1", name).lower().lstrip("_")

    if not getattr(settings, 'ANALYTICS_ENABLED', False):
        logger.debug('analytics_disabled')
        return

    # Return early if instance is a migration.
    if instance_name == 'Migration':
        return

    # Check if the instance has an _original_status and whether the status
    # has changed. If not then skip recording this save event. This can be
    # skipped if the record has been created as we will always record metrics
    # for a newly created record.
    try:
        if not created and instance._original_status == instance.status:
            return
    except AttributeError:
        pass

    # Return early if the instance doesn't have an Analytics class
    # or there is no tenant schema set.
    try:
        analytics_cls = instance.Analytics
        tenant_name = connection.schema_name
    except AttributeError:
        return

    analytics = analytics_cls()

    # Check if the analytics class for the instance has a skip
    # method and return if skip return true, otherwise continue
    try:
        if analytics.skip(instance, created):
            return
    except AttributeError:
        pass

    try:
        timestamp = analytics.timestamp(instance, created)
    except AttributeError:
        timestamp = timezone.now()

    # Check for instance specific tags
    try:
        tags = analytics.extra_tags(instance, created)
    except AttributeError:
        tags = {}

    tags['type'] = getattr(analytics, 'type', snakecase(instance_name))
    tags['tenant'] = tenant_name

    # Process tags
    _merge_attrs(tags, analytics.tags)

    # Check for instance specific fields
    try:
        fields = analytics.extra_fields(instance, created)
    except AttributeError:
        fields = {}

    # Process fields
    _merge_attrs(fields, analytics.fields)

    # If enabled, use celery to queue task
    if getattr(properties, 'CELERY_RESULT_BACKEND', None):
        queue_analytics_record.delay(timestamp=timestamp, tags=tags, fields=fields)
    else:
        queue_analytics_record(timestamp=timestamp, tags=tags, fields=fields)
