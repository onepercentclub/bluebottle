import re
from social_django.strategy import DjangoStrategy
from bluebottle.members.models import FacebookAuthentication, GoogleAuthentication


class DRFStrategy(DjangoStrategy):
    authentication_methods = {
        'facebook': FacebookAuthentication,
        'google': GoogleAuthentication,
    }

    name_mapping = {
        'KEY': 'client_id',
        'SECRET': 'secret'
    }

    def request_data(self, merge=True):
        return self.request.data

    def get_setting(self, name):
        try:
            match = re.match(r'^SOCIAL_AUTH_(FACEBOOK|GOOGLE)_(\w+)$', name)

            (backend, matched_name) = match.groups()
            authentication_method = self.authentication_methods[backend.lower()].load()

            matched_name = self.name_mapping.get(matched_name, 'invalid')

            return getattr(authentication_method, matched_name)
        except AttributeError:
            return super(DRFStrategy, self).get_setting(name)
