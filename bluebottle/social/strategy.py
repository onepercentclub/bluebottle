import re
from social_django.strategy import DjangoStrategy
from bluebottle.clients import properties
from bluebottle.members.models import SocialLoginSettings


class DRFStrategy(DjangoStrategy):
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
            settings = SocialLoginSettings.objects.get(backend=backend.lower())

            matched_name = self.name_mapping.get(matched_name, 'invalid')

            return getattr(settings, matched_name)
        except (SocialLoginSettings.DoesNotExist, AttributeError):
            try:
                return getattr(properties, name)
            except AttributeError:
                return super(DRFStrategy, self).get_setting(name)
