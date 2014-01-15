from datetime import timedelta

from django.utils.timezone import now

import factory
import factory.fuzzy

from bluebottle.tasks.models import Task, TaskMember

from .accounts import BlueBottleUserFactory
from .projects import ProjectFactory


class TaskFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Task

    author = factory.SubFactory(BlueBottleUserFactory)
    project = factory.SubFactory(ProjectFactory)
    title = factory.Sequence(lambda n: 'Task_{0}'.format(n))
    deadline = factory.fuzzy.FuzzyDateTime(now(), now() + timedelta(weeks=4))


class TaskMemberFactory(factory.DjangoModelFactory):
    FACTORY_FOR = TaskMember

    task = factory.SubFactory(TaskFactory)
    member = factory.SubFactory(BlueBottleUserFactory)
