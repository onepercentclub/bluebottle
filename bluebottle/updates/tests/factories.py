import json

import factory.fuzzy
from faker import Faker

from bluebottle.deeds.tests.factories import DeedFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.updates.models import Update

faker = Faker()


def quill_message(html=None):
    if html is None:
        html = faker.sentence()
    return json.dumps({'html': html, 'delta': ''})


def normalize_quill_message(value):
    if value is None:
        return None
    if isinstance(value, str):
        if value == '':
            return quill_message('')
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict) and 'html' in parsed:
                return value
        except json.JSONDecodeError:
            pass
        return quill_message(value)
    return value


class UpdateFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Update

    message = factory.LazyFunction(quill_message)
    author = factory.SubFactory(BlueBottleUserFactory)
    activity = factory.SubFactory(DeedFactory)
    parent = None

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        if 'message' in kwargs:
            kwargs['message'] = normalize_quill_message(kwargs['message'])
        return super()._create(model_class, *args, **kwargs)
