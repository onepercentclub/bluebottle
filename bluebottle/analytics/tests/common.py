class FakeInfluxDBClient():
    def __init__(self, *args):
        pass

    def write_points(self, **kwargs):
        pass


class FakeModel():
    class Analytics:
        type = 'fake'
        tags = {}
        fields = {}