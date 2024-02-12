from datetime import timedelta, date

import factory.fuzzy
from django.utils.timezone import now

from bluebottle.fsm.factory import FSMModelFactory
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.geo import GeolocationFactory
from bluebottle.time_based.models import (
    DateActivity, PeriodActivity,
    DateParticipant, PeriodParticipant, TimeContribution, DateActivitySlot, SlotParticipant, Skill, TeamSlot,
    DeadlineActivity, DeadlineRegistration, DeadlineParticipant
)
from bluebottle.utils.models import Language


class SkillFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = Skill

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = super(SkillFactory, cls)._create(model_class, *args, **kwargs)
        for language in Language.objects.all():
            obj.set_current_language(language.code)
            obj.name = "Name {} {}".format(language.code, obj.id)
            obj.description = "Description {} {}".format(language.code, obj.id)
        obj.save()
        return obj


class TimeBasedFactory(factory.DjangoModelFactory):
    title = factory.Faker('sentence')
    description = factory.Faker('text')

    owner = factory.SubFactory(BlueBottleUserFactory)
    initiative = factory.SubFactory(InitiativeFactory)
    capacity = 10
    review = False

    expertise = factory.SubFactory(SkillFactory)
    registration_deadline = (now() + timedelta(weeks=1)).date()


class DateActivitySlotFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = DateActivitySlot

    title = factory.Faker('sentence')
    capacity = 10
    is_online = False

    location = factory.SubFactory(GeolocationFactory)
    start = now() + timedelta(weeks=4)
    duration = timedelta(hours=2)


class DateActivityFactory(TimeBasedFactory):
    class Meta:
        model = DateActivity

    slot_selection = 'all'
    expertise = factory.SubFactory(SkillFactory)

    slots = factory.RelatedFactory(
        DateActivitySlotFactory,
        factory_related_name='activity'
    )


class PeriodActivityFactory(TimeBasedFactory):
    class Meta:
        model = PeriodActivity

    deadline = date.today() + timedelta(weeks=4)
    duration = timedelta(hours=20)
    duration_period = 'overall'
    is_online = False
    location = factory.SubFactory(GeolocationFactory)
    expertise = factory.SubFactory(SkillFactory)

    start = (now() + timedelta(weeks=2)).date()


class DeadlineActivityFactory(TimeBasedFactory):

    class Meta:
        model = DeadlineActivity

    deadline = date.today() + timedelta(weeks=4)
    registration_deadline = date.today() - timedelta(weeks=4)
    duration = timedelta(hours=4)
    is_online = False
    location = factory.SubFactory(GeolocationFactory)
    expertise = factory.SubFactory(SkillFactory)

    start = (now() - timedelta(weeks=2)).date()


class DateParticipantFactory(FSMModelFactory):
    class Meta(object):
        model = DateParticipant

    activity = factory.SubFactory(DateActivityFactory)
    user = factory.SubFactory(BlueBottleUserFactory)


class PeriodParticipantFactory(FSMModelFactory):
    class Meta(object):
        model = PeriodParticipant

    activity = factory.SubFactory(PeriodActivityFactory)
    user = factory.SubFactory(BlueBottleUserFactory)


class ParticipationFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = TimeContribution

    contributor = factory.SubFactory(PeriodParticipantFactory)

    value = timedelta(hours=20)

    start = now() + timedelta(weeks=2)
    end = now() + timedelta(weeks=3)


class SlotParticipantFactory(FSMModelFactory):
    class Meta(object):
        model = SlotParticipant

    slot = factory.SubFactory(DateActivitySlotFactory)
    participant = factory.SubFactory(DateParticipantFactory)


class TeamSlotFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = TeamSlot

    is_online = False
    location = factory.SubFactory(GeolocationFactory)
    start = now() + timedelta(weeks=4)
    duration = timedelta(hours=2)


class DeadlineRegistrationFactory(FSMModelFactory):
    class Meta(object):
        model = DeadlineRegistration

    activity = factory.SubFactory(DeadlineActivityFactory)
    user = factory.SubFactory(BlueBottleUserFactory)


class DeadlineParticipantFactory(FSMModelFactory):
    class Meta(object):
        model = DeadlineParticipant

    activity = factory.SubFactory(DeadlineActivityFactory)
    user = factory.SubFactory(BlueBottleUserFactory)
