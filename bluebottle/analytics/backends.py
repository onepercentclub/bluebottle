from influxdb import InfluxDBClient

from django.conf import settings


class InfluxExporter:
    def __init__(self, conf):
        self.measurement = conf['measurement']
        self.domain = conf['domain']
        self.port = conf['port']
        self.username = conf['username']
        self.password = conf['password']
        self.database = conf['database']

        self.client = self._client()

    def _client(self):
        return InfluxDBClient(self.domain, self.port, self.username,
                              self.password, self.database)

    def process(self, timestamp, tags={}, fields={}):
        json_body = [
            {
                "measurement": self.measurement,
                "time": timestamp ,
                "tags": tags,
                "fields": fields
            }
        ]

        self.client.write_points(json_body)
