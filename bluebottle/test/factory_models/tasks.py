from builtins import object
import factory.fuzzy

from bluebottle.time_based.models import Skill


class SkillFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Skill

    name = factory.Sequence(lambda n: 'Skill_{0}'.format(n))
