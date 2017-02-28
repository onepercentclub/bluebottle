class FakeInfluxDBClient():
    def __init__(self, *args):
        pass

    def client(self, *args, **kwargs):
        pass

    def write_points(self, *args, **kwargs):
        pass


class FakeModel():
    class Analytics:
        type = 'fake'
        tags = {}
        fields = {}


class FakeModelTwo():
    class Analytics:
        tags = {}
        fields = {}
