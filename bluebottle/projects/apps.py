from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class ProjectsAppConfig(AppConfig):
    name = 'bluebottle.projects'
    verbose_name = _('Projects')
