from datetime import timedelta

import factory.fuzzy
from django.utils.timezone import now

from bluebottle.assignments.models import Applicant, Assignment
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory
from bluebottle.test.factory_models.tasks import SkillFactory


class AssignmentFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = Assignment

    title = factory.Faker('sentence')
    description = factory.Faker('text')
    owner = factory.SubFactory(BlueBottleUserFactory)
    initiative = factory.SubFactory(InitiativeFactory)
    expertise = factory.SubFactory(SkillFactory)
    is_online = True
    duration = 4
    end_date_type = 'deadline'
    end_date = (now() + timedelta(weeks=3)).date()
    capacity = 3
    registration_deadline = (now() + timedelta(weeks=2)).date()


class ApplicantFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Applicant

    activity = factory.SubFactory(AssignmentFactory)
    user = factory.SubFactory(BlueBottleUserFactory)
