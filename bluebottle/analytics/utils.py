import logging

from celery import shared_task
from django.conf import settings

from bluebottle.utils.utils import get_class

logger = logging.getLogger(__name__)


@shared_task
def queue_analytics_record(timestamp, tags={}, fields={}):
    try:
        # TODO: logging to multiple backends could happen here, eg
        #       to influxdb and to log file.
        backend = settings.ANALYTICS_BACKENDS['default']
        handler_class = backend['handler_class']
    except AttributeError as e:
        logger.warning('Analytics backend not found: {0}'.format(e.message))
        return

    handler = get_class(handler_class)(conf=backend)
    handler.process(timestamp, tags, fields)
