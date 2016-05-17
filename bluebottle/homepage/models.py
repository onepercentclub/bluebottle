from bluebottle.quotes.models import Quote
from bluebottle.slides.models import Slide
from bluebottle.statistics.models import Statistic
from bluebottle.projects.models import Project


class HomePage(object):
    """
    Instead of serving all the objects separately we combine
    Slide, Quote and Stats into a dummy object
    """
    def get(self, language):
        self.id = language
        self.quotes = Quote.objects.published().filter(language=language)
        self.slides = Slide.objects.published().filter(language=language)
        self.statistics = Statistic.objects.filter(active=True, language=language).all()

        projects = Project.objects.filter(is_campaign=True,
                                                status__viewable=True)
        if language == 'en':
            projects = projects.filter(language__code=language)

        projects = projects.order_by('?')

        if len(projects) > 4:
            self.projects = projects[0:4]
        elif len(projects) > 0:
            self.projects = projects[0:len(projects)]
        else:
            self.projects = None

        return self
