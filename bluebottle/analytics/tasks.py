import logging
from datetime import datetime, timedelta

from celery import shared_task
from django.conf import settings
from django.core.management import call_command

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


@shared_task
def generate_engagement_metrics():
    # Generate metrics for the today till current time. The timestamp will be of the end date and hence in the future.
    # A point is uniquely identified by the measurement name, tag set, and timestamp. If you submit Line Protocol with
    # the same measurement, tag set, and timestamp, but with a different field set, the field set becomes the union of
    # the old field set and the new field set, where any conflicts favor the new field set.
    # https://docs.influxdata.com/influxdb/v1.2/write_protocols/line_protocol_tutorial/#duplicate-points
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    logger.info("Generating Engagement Metrics: start date: {} end date: {}".format(today, tomorrow))
    call_command('export_engagement_metrics', '--start', today.strftime('%Y-%m-%d'),
                 '--end', tomorrow.strftime('%Y-%m-%d'), '--export-to', 'influxdb')


@shared_task
def generate_participation_metrics(tenant, email, start_year, end_year):
    logger.info("Generating Participation Metrics: Tenant: {} Email: {} Start Year: {} End Year: {}".format(
        tenant, email, start_year, end_year
    ))
    call_command('export_participation_metrics', '--start', start_year, '--end', end_year, '--tenant', tenant)
