from datetime import timedelta

import factory.fuzzy
from django.utils.timezone import now

from bluebottle.assignments.models import Applicant, Assignment
from bluebottle.initiatives.tests.factories import InitiativeFactory
from bluebottle.test.factory_models.accounts import BlueBottleUserFactory


class AssignmentFactory(factory.DjangoModelFactory):

    class Meta(object):
        model = Assignment

    title = factory.Faker('sentence')
    description = factory.Faker('text')
    owner = factory.SubFactory(BlueBottleUserFactory)
    initiative = factory.SubFactory(InitiativeFactory)

    capacity = 3
    deadline = factory.fuzzy.FuzzyDateTime(now(), now() + timedelta(weeks=5))
    registration_deadline = factory.fuzzy.FuzzyDateTime(now(), now() + timedelta(weeks=2))


class ApplicantFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Applicant

    activity = factory.SubFactory(AssignmentFactory)
    user = factory.SubFactory(BlueBottleUserFactory)
