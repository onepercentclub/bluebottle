
class BaseMessageAdapter(object):

    def __init__(self, message):
        self.message = message

    def send(self):
        raise NotImplementedError()
