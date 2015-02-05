import factory
import factory.fuzzy
from datetime import timedelta
from django.utils.timezone import now
from bluebottle.utils.model_dispatcher import get_model_class
from bluebottle.suggestions.models import Suggestion
from .projects import ProjectFactory


class SuggestionFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Suggestion

    deadline = factory.fuzzy.FuzzyDateTime(now(), now() + timedelta(weeks=4))
    project = factory.SubFactory(ProjectFactory)
