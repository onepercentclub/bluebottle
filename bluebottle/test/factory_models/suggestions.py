import factory
import factory.fuzzy
from datetime import timedelta
from django.utils.timezone import now
from bluebottle.suggestions.models import Suggestion
from .projects import ProjectFactory, ProjectThemeFactory


class SuggestionFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Suggestion

    deadline = factory.fuzzy.FuzzyDateTime(now(), now() + timedelta(weeks=4))
    project = factory.SubFactory(ProjectFactory)
    theme = factory.SubFactory(ProjectThemeFactory)
