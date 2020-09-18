from builtins import object
import factory

from bluebottle.bb_projects.models import ProjectTheme


class ProjectThemeFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = ProjectTheme
        django_get_or_create = ('slug',)

    name = factory.Sequence(lambda n: 'Theme_{0}'.format(n))
    slug = name
    description = 'ProjectTheme factory model'
