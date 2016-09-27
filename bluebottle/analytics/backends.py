import logging

from influxdb import InfluxDBClient
from influxdb.client import InfluxDBClientError

logger = logging.getLogger(__name__)


class InfluxExporter:
    def __init__(self, conf):
        self.measurement = conf['measurement']
        self.domain = conf['domain']
        self.port = conf['port']
        self.username = conf['username']
        self.password = conf['password']
        self.database = conf['database']

    @property
    def client(self):
        return InfluxDBClient(self.domain, self.port, self.username,
                              self.password, self.database)

    def process(self, timestamp, tags, fields):
        tags = tags or {}
        fields = fields or {}

        json_body = [
            {
                "measurement": self.measurement,
                "time": timestamp ,
                "tags": tags,
                "fields": fields
            }
        ]

        try:
            self.client.write_points(json_body)
        except InfluxDBClientError as e:
            logger.exception('Failed to write to InfluxDB: %s', e.message,
                             exc_info=1)
