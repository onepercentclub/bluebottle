import factory.fuzzy

from bluebottle.tasks.models import Skill


class SkillFactory(factory.DjangoModelFactory):
    class Meta:
        model = Skill

    name = factory.Sequence(lambda n: f'Skill_{n}')
