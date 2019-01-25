import datetime
import factory

from django.utils import timezone

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.token_auth.models import CheckedToken


class CheckedTokenFactory(factory.DjangoModelFactory):
    token = '7baTf5AVWkpkiACH6nNZZUVzZR0rye7rbiqrm3Qrgph5Sn3EwsFERytBwoj2aqS' \
            'dISPvvc7aefusFmHDXAJbwLvCJ3N73x4whT7XPiJz7kfrFKYal6WlD8lu5JZgVT' \
            'mV5hdywGQkPMFT1Z7m4z1ga6Oud2KoQNhrf5cKzQ5CSdTojZmZ0FT24jBuwm5YU' \
            'qFbvwTBxg=='
    timestamp = datetime.datetime(2012, 12, 18, 11, 51, 15).replace(
        tzinfo=timezone.get_current_timezone())
    user = factory.SubFactory(BlueBottleUserFactory)

    class Meta:
        model = CheckedToken
