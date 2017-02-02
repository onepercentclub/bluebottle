import logging

from celery import shared_task
from django.conf import settings

from bluebottle.utils.utils import get_class
from .exception import AnalyticsException

logger = logging.getLogger(__name__)

@shared_task
def queue_analytics_record(timestamp, tags, fields):
    tags = tags or {}
    fields = fields or {}

    def _log(message):
        logger.warning(message, exc_info=1)

    for _, backend in getattr(settings, 'ANALYTICS_BACKENDS', {}).iteritems():
        try:
            _process_handler(backend, timestamp, tags, fields)
        except AttributeError as exc:
            _log('Analytics backend not found: {}'.format(exc.message))
        except AnalyticsException as exc:
            _log('Analytics exception: {}'.format(exc.message))
        except Exception as exc:
            _log('Unexpected analytics exception: {}'.format(exc.message))


def _process_handler(backend, timestamp, tags, fields):
    try:
        handler_class = backend['handler_class']
        handler = get_class(handler_class)(conf=backend)
        handler.process(timestamp, tags, fields)
    except Exception as exc:
        raise AnalyticsException(exc)
