from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class AssignmentAppConfig(AppConfig):
    name = 'bluebottle.assignments'
    verbose_name = _('Tasks')
