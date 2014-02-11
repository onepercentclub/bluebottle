import math
from bluebottle.slides.models import Slide
from bluebottle.bb_projects import get_project_model
from bluebottle.quotes.models import Quote
from bluebottle.tasks.models import Task
from django.db.models import Q

PROJECT_MODEL = get_project_model()


class HomePage(object):
    def get(self, language):
        language = language.replace('-', '_')
        self.id = 1
        self.quotes = Quote.objects.published().filter(language__iexact=language)
        self.slides = Slide.objects.published().filter(language__iexact=language)

        projects = PROJECT_MODEL.objects.filter(status__viewable=True).order_by('?')
        if len(projects) > 4:
            self.projects = projects[0:4]
        elif len(projects) > 0:
            self.projects = projects[0:len(projects)]
        else:
            self.projects = None

        self.project_count = PROJECT_MODEL.objects.filter(
            Q(status=4) | Q(status=5) ).count()

        self.destination_count = projects.distinct("country").count()
        tasks = Task.objects.filter(
            Q(status="realized")
        )

        self.task_count = tasks.count()
        hours = 0
        for task in tasks:
            hours += int(task.time_needed)
        self.total_hours = hours

        return self
