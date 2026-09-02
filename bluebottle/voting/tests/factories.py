import factory

from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.voting.models import Poll, PollOption, PollVote


class PollFactory(factory.DjangoModelFactory):
    class Meta:
        model = Poll

    status = 'open'

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        title = kwargs.pop('title', 'Test poll')
        subtitle = kwargs.pop('subtitle', '')
        obj = model_class(*args, **kwargs)
        obj.set_current_language('en')
        obj.title = title
        obj.subtitle = subtitle
        obj.save()
        return obj


class PollOptionFactory(factory.DjangoModelFactory):
    class Meta:
        model = PollOption

    poll = factory.SubFactory(PollFactory)

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        title = kwargs.pop('title', 'Option')
        kwargs.pop('description', None)
        obj = model_class(*args, **kwargs)
        obj.set_current_language('en')
        obj.title = title
        obj.save()
        return obj


class PollVoteFactory(factory.DjangoModelFactory):
    class Meta:
        model = PollVote

    option = factory.SubFactory(PollOptionFactory)
    poll = factory.SelfAttribute('option.poll')
    owner = factory.SubFactory(BlueBottleUserFactory)
