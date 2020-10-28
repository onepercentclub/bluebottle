import factory

from bluebottle.bb_projects.models import ProjectTheme


class ProjectThemeFactory(factory.DjangoModelFactory):
    class Meta:
        model = ProjectTheme
        django_get_or_create = ('slug',)

    name = factory.Sequence(lambda n: f'Theme_{n}')
    slug = name
    description = 'ProjectTheme factory model'
