import factory

from bluebottle.surveys.models import Survey


class SurveyFactory(factory.DjangoModelFactory):
    class Meta(object):
        model = Survey
