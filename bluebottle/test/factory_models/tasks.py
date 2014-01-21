from datetime import timedelta

from django.utils.timezone import now

import factory
import factory.fuzzy

from bluebottle.tasks.models import Task, TaskMember, Skill

from .accounts import BlueBottleUserFactory
from .projects import ProjectFactory


class SkillFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Skill

    name = factory.Sequence(lambda n: 'Skill_{0}'.format(n))
    name_nl = factory.LazyAttribute(lambda o: o.name)


class TaskFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Task

    author = factory.SubFactory(BlueBottleUserFactory)
    project = factory.SubFactory(ProjectFactory)
    skill = factory.SubFactory(SkillFactory)
    title = factory.Sequence(lambda n: 'Task_{0}'.format(n))
    deadline = factory.fuzzy.FuzzyDateTime(now(), now() + timedelta(weeks=4))


class TaskMemberFactory(factory.DjangoModelFactory):
    FACTORY_FOR = TaskMember

    task = factory.SubFactory(TaskFactory)
    member = factory.SubFactory(BlueBottleUserFactory)
