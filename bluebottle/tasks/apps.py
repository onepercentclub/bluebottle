from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class TasksAppConfig(AppConfig):
    name = 'bluebottle.tasks'
    verbose_name = _('Tasks')
