from bluebottle.quotes.models import Quote
from bluebottle.slides.models import Slide
from bluebottle.statistics.statistics import Statistics
from bluebottle.utils.model_dispatcher import get_project_model

PROJECT_MODEL = get_project_model()


class HomePage(object):
    """
    Instead of serving all the objects separately we combine
    Slide, Quote and Stats into a dummy object
    """
    def get(self, language):
        self.id = language
        self.quotes = Quote.objects.published().filter(language=language)
        self.slides = Slide.objects.published().filter(language=language)
        self.stats = Statistics()

        projects = PROJECT_MODEL.objects.filter(is_campaign=True,
                                                status__viewable=True)
        if language == 'en':
            projects = projects.filter(language__code=language)

        projects = projects.order_by('?')

        if len(projects) > 3:
            self.projects = projects[0:3]
        elif len(projects) > 0:
            self.projects = projects[0:len(projects)]
        else:
            self.projects = None

        return self
