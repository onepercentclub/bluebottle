from datetime import timedelta

from django.utils.timezone import now

import factory
import factory.fuzzy

from bluebottle.utils.model_dispatcher import get_task_model, get_taskmember_model, get_task_skill_model
from .accounts import BlueBottleUserFactory
from .projects import ProjectFactory

TASK_MODEL = get_task_model()
TASK_MEMBER_MODEL = get_taskmember_model()
TASK_SKILL_MODEL = get_task_skill_model()


class SkillFactory(factory.DjangoModelFactory):
    FACTORY_FOR = TASK_SKILL_MODEL

    name = factory.Sequence(lambda n: 'Skill_{0}'.format(n))
    name_nl = factory.LazyAttribute(lambda o: o.name)


class TaskFactory(factory.DjangoModelFactory):
    FACTORY_FOR = TASK_MODEL

    author = factory.SubFactory(BlueBottleUserFactory)
    project = factory.SubFactory(ProjectFactory)
    skill = factory.SubFactory(SkillFactory)
    title = factory.Sequence(lambda n: 'Task_{0}'.format(n))
    deadline = factory.fuzzy.FuzzyDateTime(now(), now() + timedelta(weeks=4))
    description = factory.Sequence(lambda n: "Filler description text{0}".format(n))
    location = factory.Sequence(lambda n: "Location_{0}".format(n))
    time_needed = 4


    @factory.post_generation
    def members(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for member in extracted:
                self.members.add(member)


class TaskMemberFactory(factory.DjangoModelFactory):
    FACTORY_FOR = TASK_MEMBER_MODEL

    member = factory.SubFactory(BlueBottleUserFactory)
    status = 'accepted'

    task = factory.SubFactory(TaskFactory)
