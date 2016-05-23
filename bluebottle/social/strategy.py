from social.strategies.django_strategy import DjangoStrategy
from bluebottle.clients import properties


class DRFStrategy(DjangoStrategy):
    def request_data(self, merge=True):
        return self.request.data

    def get_setting(self, name):
        try:
            return getattr(properties, name)
        except AttributeError:
            return super(DRFStrategy, self).get_setting(name)
