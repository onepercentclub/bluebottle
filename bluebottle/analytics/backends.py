import json
import logging
import os
from datetime import datetime
from numbers import Integral

from influxdb import InfluxDBClient
from influxdb.client import InfluxDBClientError
from pytz import UTC

from .exception import AnalyticsException

logger = logging.getLogger(__name__)

EPOCH = UTC.localize(datetime.utcfromtimestamp(0))
TIME_PRECISION = 'u'


def _convert_timestamp(timestamp):
    if isinstance(timestamp, Integral):
        # assume precision is correct if timestamp is int
        return timestamp
    if isinstance(timestamp, datetime):
        # convert datetime to unix timestamp (with TIME_PRECISION)
        if not timestamp.tzinfo:
            timestamp = UTC.localize(timestamp)

        sec = (timestamp - EPOCH).total_seconds()

        def _handle_precision():
            if TIME_PRECISION == 'n':
                return sec * 1e9
            elif TIME_PRECISION == 'u':
                return sec * 1e6
            elif TIME_PRECISION == 'ms':
                return sec * 1e3
            elif TIME_PRECISION == 's':
                return sec

            msg = 'Unhandled TIME_PRECISION of \'{}\''.format(TIME_PRECISION)
            raise AnalyticsException(msg)

        return int(_handle_precision())


def to_influx_json(measurement, timestamp, tags, fields):
    tags = tags or {}
    fields = fields or {}

    return [
        {
            "measurement": measurement,
            "time": _convert_timestamp(timestamp),
            "tags": tags,
            "fields": fields
        }
    ]


class InfluxExporter:
    def __init__(self, conf):
        self.measurement = conf['measurement']
        self.host = conf['host']
        self.port = conf['port']
        self.username = conf['username']
        self.password = conf['password']
        self.database = conf['database']
        self.ssl = conf['ssl']

    @property
    def client(self):
        return InfluxDBClient(host=self.host, port=self.port, username=self.username,
                              password=self.password, database=self.database,
                              ssl=self.ssl)

    def process(self, timestamp, tags, fields):
        json_body = to_influx_json(self.measurement, timestamp, tags, fields)

        try:
            self.client.write_points(json_body, time_precision=TIME_PRECISION)
        except InfluxDBClientError as err:
            logger.exception('Failed to write to InfluxDB: %s', err.message,
                             exc_info=1)


class FileExporter:
    def __init__(self, conf):
        self.base_dir = conf['base_dir']
        self.measurement = conf['measurement']

    def process(self, timestamp, tags, fields):
        json_body = to_influx_json(self.measurement, timestamp, tags, fields)
        batch = timestamp.strftime('%Y-%m-%d')

        tenant_dir = os.path.join(self.base_dir, tags.get('tenant', 'common'))
        if not os.path.exists(tenant_dir):
            os.makedirs(tenant_dir)
        logname = os.path.join(tenant_dir, '{}.log'.format(batch))

        try:
            with open(logname, 'ab') as log:
                log.write(json.dumps(json_body) + '\n')
        except StandardError as err:
            logger.exception('Failed to write to InfluxDB log: %s', err.message,
                             exc_info=1)
