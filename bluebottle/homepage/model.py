from bluebottle.slides.models import Slide
from bluebottle.projects import get_project_model
from bluebottle.quotes.models import Quote

PROJECT_MODEL = get_project_model()


class HomePage(object):
    def get(self, language):
        self.id = 1
        self.quotes = Quote.objects.published().filter(language=language)
        self.slides = Slide.objects.published().filter(language=language)

        projects = PROJECT_MODEL.objects.filter(status__viewable=True).order_by('?')
        if len(projects) > 4:
            self.projects = projects[0:4]
        elif len(projects) > 0:
            self.projects = projects[0:len(projects)]
        else:
            self.projects = None

        return self
