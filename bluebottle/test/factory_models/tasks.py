from datetime import timedelta

from django.utils.timezone import now

import factory
import factory.fuzzy

from bluebottle.tasks.models import Skill, Task, TaskMember
from .accounts import BlueBottleUserFactory
from .projects import ProjectFactory


class SkillFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Skill

    name = factory.Sequence(lambda n: 'Skill_{0}'.format(n))


class TaskFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Task

    author = factory.SubFactory(BlueBottleUserFactory)
    project = factory.SubFactory(ProjectFactory)
    skill = factory.SubFactory(SkillFactory)
    title = factory.Sequence(lambda n: 'Task_{0}'.format(n))
    deadline = factory.fuzzy.FuzzyDateTime(now(), now() + timedelta(weeks=4))
    deadline_to_apply = factory.fuzzy.FuzzyDateTime(now(), now() + timedelta(weeks=3))
    description = factory.Sequence(
        lambda n: "Filler description text{0}".format(n))
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
    class Meta(object):
        model = TaskMember

    member = factory.SubFactory(BlueBottleUserFactory)
    status = 'accepted'

    task = factory.SubFactory(TaskFactory)

    @classmethod
    def create(cls, *args, **kwargs):
        created = kwargs.pop('created', None)
        obj = super(TaskMemberFactory, cls).create(*args, **kwargs)
        if created is not None:
            obj.created = created
            obj.save()
        return obj
